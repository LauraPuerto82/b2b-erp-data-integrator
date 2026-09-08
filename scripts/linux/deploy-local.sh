#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

export UV_PROJECT_ENVIRONMENT="$PROJECT_ROOT/.venv-linux"

AWS_ENDPOINT="http://localhost:4566"
AWS_REGION="us-east-1"

MINISTACK_CONTAINER="b2b-ministack"
MINISTACK_IMAGE="ministackorg/ministack"
GLUE_DOCKER_IMAGE="public.ecr.aws/glue/aws-glue-libs:5"

BUCKET_NAME="b2b-erp-data-integrator-local"
GLUE_JOB_NAME="b2b-erp-data-integrator-customers"
GLUE_ROLE_NAME="b2b-erp-data-integrator-glue-role"
GLUE_VERSION="5.0"

export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="$AWS_REGION"

echo "B2B ERP Data Integrator - Local deployment"
echo "Project root: $PROJECT_ROOT"

echo
echo "Checking required tools..."

for tool in docker aws uv; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Required tool not found: $tool" >&2
        exit 1
    fi
done

echo "Required tools are available."

echo
echo "Checking Docker..."

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running." >&2
    exit 1
fi

echo "Docker is running."

install_docker_image() {
    local image="$1"

    if docker image inspect "$image" >/dev/null 2>&1; then
        echo "Docker image available: $image"
        return
    fi

    echo "Pulling Docker image: $image"

    if ! docker pull "$image"; then
        echo "Failed to pull Docker image: $image" >&2
        exit 1
    fi
}

echo
echo "Checking Docker images..."

install_docker_image "$MINISTACK_IMAGE"
install_docker_image "$GLUE_DOCKER_IMAGE"

echo "Docker images are available."

echo
echo "Starting MiniStack..."

if docker container inspect "$MINISTACK_CONTAINER" >/dev/null 2>&1; then
    echo "Removing existing MiniStack container..."
    docker rm -f "$MINISTACK_CONTAINER" >/dev/null
fi

docker run -d \
    --name "$MINISTACK_CONTAINER" \
    -p 4566:4566 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e "GLUE_DOCKER_IMAGE=$GLUE_DOCKER_IMAGE" \
    "$MINISTACK_IMAGE" >/dev/null

echo "MiniStack container started."

echo "Waiting for MiniStack to become healthy..."

MAX_ATTEMPTS=30
ATTEMPT=0

while true; do
    ATTEMPT=$((ATTEMPT + 1))

    HEALTH_STATUS="$(
        docker inspect \
            --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
            "$MINISTACK_CONTAINER"
    )"

    if [[ "$HEALTH_STATUS" == "healthy" ]]; then
        break
    fi

    if [[ "$HEALTH_STATUS" == "exited" || "$HEALTH_STATUS" == "dead" ]]; then
        echo "MiniStack stopped unexpectedly." >&2
        docker logs "$MINISTACK_CONTAINER" >&2
        exit 1
    fi

    if (( ATTEMPT >= MAX_ATTEMPTS )); then
        echo "MiniStack did not become healthy in time." >&2
        docker logs "$MINISTACK_CONTAINER" >&2
        exit 1
    fi

    sleep 1
done

echo "MiniStack is healthy."

echo
echo "Building application package..."

cd "$PROJECT_ROOT"

uv build

WHEEL_PATH="$(
    find "$PROJECT_ROOT/dist" \
        -maxdepth 1 \
        -type f \
        -name 'b2b_erp_data_integrator-*.whl' \
        -printf '%T@ %p\n' |
    sort -nr |
    head -n 1 |
    cut -d' ' -f2-
)"

if [[ -z "$WHEEL_PATH" || ! -f "$WHEEL_PATH" ]]; then
    echo "Application wheel was not generated." >&2
    exit 1
fi

WHEEL_NAME="$(basename "$WHEEL_PATH")"

echo "Application wheel built: $WHEEL_NAME"

GLUE_SCRIPT_PATH="$PROJECT_ROOT/src/b2b_erp_data_integrator/glue/main.py"

if [[ ! -f "$GLUE_SCRIPT_PATH" ]]; then
    echo "Glue entry point was not found: $GLUE_SCRIPT_PATH" >&2
    exit 1
fi

GLUE_SCRIPT_KEY="scripts/main.py"
GLUE_WHEEL_KEY="artifacts/$WHEEL_NAME"

GLUE_ROLE_ARN="arn:aws:iam::000000000000:role/$GLUE_ROLE_NAME"
GLUE_SCRIPT_URI="s3://$BUCKET_NAME/$GLUE_SCRIPT_KEY"
GLUE_WHEEL_URI="http://host.docker.internal:4566/$BUCKET_NAME/$GLUE_WHEEL_KEY"

echo
echo "Creating local S3 bucket..."

if ! aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --endpoint-url "$AWS_ENDPOINT" \
    --region "$AWS_REGION" >/dev/null; then
    echo "Failed to create S3 bucket: $BUCKET_NAME" >&2
    exit 1
fi

echo "S3 bucket created: $BUCKET_NAME"

echo
echo "Uploading deployment artifacts..."

if ! aws s3 cp \
    "$GLUE_SCRIPT_PATH" \
    "s3://$BUCKET_NAME/$GLUE_SCRIPT_KEY" \
    --endpoint-url "$AWS_ENDPOINT" \
    --region "$AWS_REGION" >/dev/null; then
    echo "Failed to upload Glue entry point." >&2
    exit 1
fi

if ! aws s3 cp \
    "$WHEEL_PATH" \
    "s3://$BUCKET_NAME/$GLUE_WHEEL_KEY" \
    --endpoint-url "$AWS_ENDPOINT" \
    --region "$AWS_REGION" >/dev/null; then
    echo "Failed to upload application wheel." >&2
    exit 1
fi

echo "Deployment artifacts uploaded."

echo
echo "Creating local Glue IAM role..."

TRUST_POLICY_PATH="$(mktemp)"
S3_POLICY_PATH="$(mktemp)"

cat > "$TRUST_POLICY_PATH" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "glue.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

cat > "$S3_POLICY_PATH" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::$BUCKET_NAME"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    }
  ]
}
EOF

if ! aws iam create-role \
    --role-name "$GLUE_ROLE_NAME" \
    --assume-role-policy-document "file://$TRUST_POLICY_PATH" \
    --endpoint-url "$AWS_ENDPOINT" \
    --region "$AWS_REGION" >/dev/null; then
    echo "Failed to create Glue IAM role: $GLUE_ROLE_NAME" >&2
    exit 1
fi

if ! aws iam put-role-policy \
    --role-name "$GLUE_ROLE_NAME" \
    --policy-name "GlueS3Access" \
    --policy-document "file://$S3_POLICY_PATH" \
    --endpoint-url "$AWS_ENDPOINT" \
    --region "$AWS_REGION" >/dev/null; then
    echo "Failed to attach S3 policy to Glue IAM role." >&2
    exit 1
fi

echo "Glue IAM role created."

CREATED_GLUE_ROLE_ARN="$(
    aws iam get-role \
        --role-name "$GLUE_ROLE_NAME" \
        --endpoint-url "$AWS_ENDPOINT" \
        --region "$AWS_REGION" \
        --query "Role.Arn" \
        --output text
)"

if [[ -z "$CREATED_GLUE_ROLE_ARN" ]]; then
    echo "Failed to verify Glue IAM role." >&2
    exit 1
fi

if [[ "$CREATED_GLUE_ROLE_ARN" != "$GLUE_ROLE_ARN" ]]; then
    echo "Unexpected Glue IAM role ARN: $CREATED_GLUE_ROLE_ARN" >&2
    exit 1
fi

echo "Glue IAM role verified."

rm -f "$TRUST_POLICY_PATH" "$S3_POLICY_PATH"

echo
echo "Creating local Glue job..."

GLUE_COMMAND_PATH="$(mktemp)"
GLUE_DEFAULT_ARGUMENTS_PATH="$(mktemp)"

cat > "$GLUE_COMMAND_PATH" <<EOF
{
  "Name": "glueetl",
  "ScriptLocation": "$GLUE_SCRIPT_URI",
  "PythonVersion": "3"
}
EOF

cat > "$GLUE_DEFAULT_ARGUMENTS_PATH" <<EOF
{
  "--job-language": "python",
  "--additional-python-modules": "$GLUE_WHEEL_URI"
}
EOF

if ! aws glue create-job \
    --name "$GLUE_JOB_NAME" \
    --role "$GLUE_ROLE_ARN" \
    --command "file://$GLUE_COMMAND_PATH" \
    --glue-version "$GLUE_VERSION" \
    --worker-type "G.1X" \
    --number-of-workers 2 \
    --default-arguments "file://$GLUE_DEFAULT_ARGUMENTS_PATH" \
    --endpoint-url "$AWS_ENDPOINT" \
    --region "$AWS_REGION" >/dev/null; then
    echo "Failed to create local Glue job: $GLUE_JOB_NAME" >&2
    exit 1
fi

echo "Local Glue job created."

rm -f "$GLUE_COMMAND_PATH" "$GLUE_DEFAULT_ARGUMENTS_PATH"

echo
echo "Verifying local Glue job..."

CREATED_GLUE_VERSION="$(
    aws glue get-job \
        --job-name "$GLUE_JOB_NAME" \
        --endpoint-url "$AWS_ENDPOINT" \
        --region "$AWS_REGION" \
        --query "Job.GlueVersion" \
        --output text
)"

CREATED_SCRIPT_LOCATION="$(
    aws glue get-job \
        --job-name "$GLUE_JOB_NAME" \
        --endpoint-url "$AWS_ENDPOINT" \
        --region "$AWS_REGION" \
        --query "Job.Command.ScriptLocation" \
        --output text
)"

CREATED_WHEEL_URI="$(
    aws glue get-job \
        --job-name "$GLUE_JOB_NAME" \
        --endpoint-url "$AWS_ENDPOINT" \
        --region "$AWS_REGION" \
        --query "Job.DefaultArguments.\"--additional-python-modules\"" \
        --output text
)"

if [[ "$CREATED_GLUE_VERSION" != "$GLUE_VERSION" ]]; then
    echo "Unexpected Glue version: $CREATED_GLUE_VERSION" >&2
    exit 1
fi

if [[ "$CREATED_SCRIPT_LOCATION" != "$GLUE_SCRIPT_URI" ]]; then
    echo "Unexpected Glue script location: $CREATED_SCRIPT_LOCATION" >&2
    exit 1
fi

if [[ "$CREATED_WHEEL_URI" != "$GLUE_WHEEL_URI" ]]; then
    echo "Unexpected Glue wheel URI: $CREATED_WHEEL_URI" >&2
    exit 1
fi

echo "Local Glue job verified."

echo
echo "Local deployment completed successfully."
