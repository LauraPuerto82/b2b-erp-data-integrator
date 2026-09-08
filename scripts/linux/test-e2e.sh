#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

export UV_PROJECT_ENVIRONMENT="$PROJECT_ROOT/.venv-linux"

AWS_ENDPOINT="http://localhost:4566"
AWS_REGION="us-east-1"

BUCKET_NAME="b2b-erp-data-integrator-local"
GLUE_JOB_NAME="b2b-erp-data-integrator-customers"

export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="$AWS_REGION"

echo "B2B ERP Data Integrator - End-to-end test"
echo "Project root: $PROJECT_ROOT"

echo
echo "Checking local deployment..."

if ! aws s3api head-bucket \
    --bucket "$BUCKET_NAME" \
    --endpoint-url "$AWS_ENDPOINT" \
    --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "Local S3 bucket '$BUCKET_NAME' was not found. Run deploy-local.sh first." >&2
    exit 1
fi

if ! aws glue get-job \
    --job-name "$GLUE_JOB_NAME" \
    --endpoint-url "$AWS_ENDPOINT" \
    --region "$AWS_REGION" >/dev/null 2>&1; then
    echo "Local Glue job '$GLUE_JOB_NAME' was not found. Run deploy-local.sh first." >&2
    exit 1
fi

echo "Local deployment is available."

DEMO_CSV_PATH="$PROJECT_ROOT/demo/erp_b_customers.csv"

if [[ ! -f "$DEMO_CSV_PATH" ]]; then
    echo "E2E demo CSV was not found: $DEMO_CSV_PATH" >&2
    exit 1
fi

INPUT_KEY="raw/erp_b/customers.csv"
INPUT_URI="s3a://$BUCKET_NAME/$INPUT_KEY"

PROCESSED_URI="s3a://$BUCKET_NAME/processed/erp_b/"
REJECTED_URI="s3a://$BUCKET_NAME/rejected/erp_b/"

echo
echo "Uploading E2E input dataset..."

if ! aws s3 cp \
    "$DEMO_CSV_PATH" \
    "s3://$BUCKET_NAME/$INPUT_KEY" \
    --endpoint-url "$AWS_ENDPOINT" \
    --region "$AWS_REGION" >/dev/null; then
    echo "Failed to upload E2E input dataset." >&2
    exit 1
fi

echo "E2E input dataset uploaded."

JOB_ARGUMENTS_PATH="$(mktemp)"

cat > "$JOB_ARGUMENTS_PATH" <<EOF
{
  "--JOB_NAME": "$GLUE_JOB_NAME",
  "--source_system": "ERP_B",
  "--input_path": "$INPUT_URI",
  "--processed_path": "$PROCESSED_URI",
  "--rejected_path": "$REJECTED_URI"
}
EOF

echo
echo "Starting Glue job..."

JOB_RUN_ID="$(
    aws glue start-job-run \
        --job-name "$GLUE_JOB_NAME" \
        --arguments "file://$JOB_ARGUMENTS_PATH" \
        --endpoint-url "$AWS_ENDPOINT" \
        --region "$AWS_REGION" \
        --query "JobRunId" \
        --output text
)"

rm -f "$JOB_ARGUMENTS_PATH"

if [[ -z "$JOB_RUN_ID" || "$JOB_RUN_ID" == "None" ]]; then
    echo "Failed to start Glue job." >&2
    exit 1
fi

echo "Glue job started: $JOB_RUN_ID"

echo
echo "Waiting for Glue job to finish..."

MAX_ATTEMPTS=60
ATTEMPT=0
JOB_RUN_STATE=""

while (( ATTEMPT < MAX_ATTEMPTS )); do
    ATTEMPT=$((ATTEMPT + 1))

    JOB_RUN_STATE="$(
        aws glue get-job-run \
            --job-name "$GLUE_JOB_NAME" \
            --run-id "$JOB_RUN_ID" \
            --endpoint-url "$AWS_ENDPOINT" \
            --region "$AWS_REGION" \
            --query "JobRun.JobRunState" \
            --output text
    )"

    if [[ "$JOB_RUN_STATE" == "SUCCEEDED" ]]; then
        break
    fi

    if [[ "$JOB_RUN_STATE" == "FAILED" ||
          "$JOB_RUN_STATE" == "STOPPED" ||
          "$JOB_RUN_STATE" == "TIMEOUT" ||
          "$JOB_RUN_STATE" == "ERROR" ]]; then

        ERROR_MESSAGE="$(
            aws glue get-job-run \
                --job-name "$GLUE_JOB_NAME" \
                --run-id "$JOB_RUN_ID" \
                --endpoint-url "$AWS_ENDPOINT" \
                --region "$AWS_REGION" \
                --query "JobRun.ErrorMessage" \
                --output text
        )"

        echo "Glue job failed with state '$JOB_RUN_STATE'." >&2
        echo "$ERROR_MESSAGE" >&2
        exit 1
    fi

    sleep 2
done

if [[ "$JOB_RUN_STATE" != "SUCCEEDED" ]]; then
    echo "Glue job did not complete successfully within $((MAX_ATTEMPTS * 2)) seconds." >&2
    exit 1
fi

echo "Glue job succeeded."

echo
echo "Verifying E2E outputs..."

PROCESSED_OBJECTS="$(
    aws s3api list-objects-v2 \
        --bucket "$BUCKET_NAME" \
        --prefix "processed/erp_b/" \
        --endpoint-url "$AWS_ENDPOINT" \
        --region "$AWS_REGION" \
        --query "Contents[?ends_with(Key, '.parquet')].Key" \
        --output text
)"

if [[ -z "$PROCESSED_OBJECTS" || "$PROCESSED_OBJECTS" == "None" ]]; then
    echo "No processed Parquet output was generated." >&2
    exit 1
fi

REJECTED_OBJECTS="$(
    aws s3api list-objects-v2 \
        --bucket "$BUCKET_NAME" \
        --prefix "rejected/erp_b/" \
        --endpoint-url "$AWS_ENDPOINT" \
        --region "$AWS_REGION" \
        --query "Contents[?ends_with(Key, '.json')].Key" \
        --output text
)"

if [[ -z "$REJECTED_OBJECTS" || "$REJECTED_OBJECTS" == "None" ]]; then
    echo "No rejected JSON output was generated." >&2
    exit 1
fi

echo "Processed and rejected outputs were generated."

E2E_TEMP_DIR="$(mktemp -d)"
PROCESSED_DIR="$E2E_TEMP_DIR/processed"
REJECTED_DIR="$E2E_TEMP_DIR/rejected"

mkdir -p "$PROCESSED_DIR" "$REJECTED_DIR"

if ! aws s3 cp \
    "s3://$BUCKET_NAME/processed/erp_b/" \
    "$PROCESSED_DIR" \
    --recursive \
    --endpoint-url "$AWS_ENDPOINT" \
    --region "$AWS_REGION" >/dev/null; then
    echo "Failed to download processed E2E output." >&2
    exit 1
fi

if ! aws s3 cp \
    "s3://$BUCKET_NAME/rejected/erp_b/" \
    "$REJECTED_DIR" \
    --recursive \
    --endpoint-url "$AWS_ENDPOINT" \
    --region "$AWS_REGION" >/dev/null; then
    echo "Failed to download rejected E2E output." >&2
    exit 1
fi

echo "Validating processed customer..."

PROCESSED_VALIDATION="$(
    uv run python -c "
import json
import pathlib
import pyarrow.parquet as pq

directory = pathlib.Path(r'$PROCESSED_DIR')
files = list(directory.glob('*.parquet'))

rows = []
for file in files:
    rows.extend(pq.read_table(file).to_pylist())

print(json.dumps(rows))
"
)"

PROCESSED_EXTERNAL_ID="$(
    printf '%s' "$PROCESSED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0]['external_id'] if len(rows) == 1 else '')"
)"

PROCESSED_NAME="$(
    printf '%s' "$PROCESSED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0]['name'] if len(rows) == 1 else '')"
)"

PROCESSED_TAX_ID="$(
    printf '%s' "$PROCESSED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0]['tax_id'] if len(rows) == 1 else '')"
)"

PROCESSED_COUNTRY="$(
    printf '%s' "$PROCESSED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0]['country'] if len(rows) == 1 else '')"
)"

PROCESSED_EMAIL="$(
    printf '%s' "$PROCESSED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0]['email'] if len(rows) == 1 else '')"
)"

PROCESSED_CUSTOMER_ID="$(
    printf '%s' "$PROCESSED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0].get('customer_id', '') if len(rows) == 1 else '')"
)"

if [[ "$PROCESSED_EXTERNAL_ID" != "C001" ||
      "$PROCESSED_NAME" != "ACME S.L." ||
      "$PROCESSED_TAX_ID" != "B12345678" ||
      "$PROCESSED_COUNTRY" != "ES" ||
      "$PROCESSED_EMAIL" != "info@acme.es" ||
      -z "$PROCESSED_CUSTOMER_ID" ]]; then
    echo "Processed customer does not match the expected E2E result." >&2
    exit 1
fi

echo "Processed customer is correct."

echo "Validating rejected customer..."

REJECTED_VALIDATION="$(
    cat "$REJECTED_DIR"/*.json |
    uv run python -c "
import json
import sys

rows = [json.loads(line) for line in sys.stdin if line.strip()]
print(json.dumps(rows))
"
)"

REJECTED_EXTERNAL_ID="$(
    printf '%s' "$REJECTED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0]['external_id'] if len(rows) == 1 else '')"
)"

REJECTED_NAME="$(
    printf '%s' "$REJECTED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0]['name'] if len(rows) == 1 else '')"
)"

REJECTED_TAX_ID="$(
    printf '%s' "$REJECTED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0]['tax_id'] if len(rows) == 1 else '')"
)"

REJECTED_COUNTRY="$(
    printf '%s' "$REJECTED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0]['country'] if len(rows) == 1 else '')"
)"

REJECTED_EMAIL="$(
    printf '%s' "$REJECTED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0]['email'] if len(rows) == 1 else '')"
)"

REJECTED_REASON="$(
    printf '%s' "$REJECTED_VALIDATION" |
    uv run python -c "import json, sys; rows=json.load(sys.stdin); print(rows[0]['reason'] if len(rows) == 1 else '')"
)"

if [[ "$REJECTED_EXTERNAL_ID" != "C002" ||
      "$REJECTED_NAME" != "Globex S.L." ||
      "$REJECTED_TAX_ID" != "B1234" ||
      "$REJECTED_COUNTRY" != "ES" ||
      "$REJECTED_EMAIL" != "info@globex.es" ||
      "$REJECTED_REASON" != "Invalid tax ID" ]]; then
    echo "Rejected customer does not match the expected E2E result." >&2
    exit 1
fi

echo "Rejected customer is correct."

rm -rf "$E2E_TEMP_DIR"

echo
echo "E2E test passed successfully."
