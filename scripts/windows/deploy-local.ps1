$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..\..").Path

$MiniStackContainerName = "b2b-ministack"
$MiniStackImage = "ministackorg/ministack"
$GlueDockerImage = "public.ecr.aws/glue/aws-glue-libs:5"

$AwsEndpoint = "http://localhost:4566"
$AwsRegion = "us-east-1"

$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:AWS_DEFAULT_REGION = $AwsRegion

$BucketName = "b2b-erp-data-integrator-local"

$GlueVersion = "5.0"
$GlueJobName = "b2b-erp-data-integrator-customers"
$GlueRoleName = "b2b-erp-data-integrator-glue-role"

Write-Host "B2B ERP Data Integrator - Local deployment"
Write-Host "Project root: $ProjectRoot"

function Test-CommandExists {
    param (
        [Parameter(Mandatory = $true)]
        [string]$CommandName
    )

    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw "Required command '$CommandName' was not found in PATH."
    }
}

Write-Host ""
Write-Host "Checking required tools..."

Test-CommandExists "docker"
Test-CommandExists "aws"
Test-CommandExists "uv"

Write-Host "Required tools are available."

Write-Host ""
Write-Host "Checking Docker..."

docker info *> $null

if ($LASTEXITCODE -ne 0) {
    throw "Docker is installed, but the Docker daemon is not available."
}

Write-Host "Docker is running."

function Install-DockerImage {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Image
    )

    docker image inspect $Image *> $null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker image available: $Image"
        return
    }

    Write-Host "Pulling Docker image: $Image"
    docker pull $Image

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to pull Docker image '$Image'."
    }
}

Write-Host ""
Write-Host "Checking Docker images..."

Install-DockerImage $MiniStackImage
Install-DockerImage $GlueDockerImage

Write-Host "Docker images are available."

Write-Host ""
Write-Host "Starting MiniStack..."

$ExistingContainer = docker ps -a `
    --filter "name=^/$MiniStackContainerName$" `
    --format "{{.Names}}"

if ($ExistingContainer -eq $MiniStackContainerName) {
    Write-Host "Removing existing MiniStack container..."
    docker rm -f $MiniStackContainerName

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to remove existing MiniStack container."
    }
}

docker run -d `
    --name $MiniStackContainerName `
    -p 4566:4566 `
    -v /var/run/docker.sock:/var/run/docker.sock `
    -e "GLUE_DOCKER_IMAGE=$GlueDockerImage" `
    $MiniStackImage

if ($LASTEXITCODE -ne 0) {
    throw "Failed to start MiniStack."
}

Write-Host "MiniStack container started."

Write-Host "Waiting for MiniStack to become healthy..."

$MaxAttempts = 30
$Attempt = 0

do {
    $Attempt++

    $HealthStatus = docker inspect `
        --format "{{.State.Health.Status}}" `
        $MiniStackContainerName 2>$null

    if ($HealthStatus -eq "healthy") {
        break
    }

    if ($HealthStatus -eq "unhealthy") {
        throw "MiniStack became unhealthy."
    }

    Start-Sleep -Seconds 1
} while ($Attempt -lt $MaxAttempts)

if ($HealthStatus -ne "healthy") {
    throw "MiniStack did not become healthy within $MaxAttempts seconds."
}

Write-Host "MiniStack is healthy."

Write-Host ""
Write-Host "Building application package..."

Push-Location $ProjectRoot

try {
    Remove-Item -Recurse -Force "dist" -ErrorAction SilentlyContinue

    uv build

    if ($LASTEXITCODE -ne 0) {
        throw "Application build failed."
    }
}
finally {
    Pop-Location
}

$WheelPath = Get-ChildItem `
    -Path "$ProjectRoot\dist" `
    -Filter "*.whl" |
Select-Object -First 1

if (-not $WheelPath) {
    throw "Application wheel was not generated."
}

Write-Host "Application wheel built: $($WheelPath.Name)"

$WheelName = $WheelPath.Name

$GlueScriptPath = Join-Path `
    $ProjectRoot `
    "src\b2b_erp_data_integrator\glue\main.py"

if (-not (Test-Path $GlueScriptPath)) {
    throw "Glue entry point was not found: $GlueScriptPath"
}

$GlueScriptKey = "scripts/main.py"
$GlueWheelKey = "artifacts/$WheelName"

$GlueRoleArn = "arn:aws:iam::000000000000:role/$GlueRoleName"
$GlueScriptUri = "s3://$BucketName/$GlueScriptKey"
$GlueWheelUri = "http://host.docker.internal:4566/$BucketName/$GlueWheelKey"

Write-Host ""
Write-Host "Creating local S3 bucket..."

aws s3api create-bucket `
    --bucket $BucketName `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion *> $null

if ($LASTEXITCODE -ne 0) {
    throw "Failed to create S3 bucket '$BucketName'."
}

Write-Host "S3 bucket created: $BucketName"

Write-Host ""
Write-Host "Uploading deployment artifacts..."

aws s3 cp `
    $GlueScriptPath `
    "s3://$BucketName/$GlueScriptKey" `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion

if ($LASTEXITCODE -ne 0) {
    throw "Failed to upload Glue entry point."
}

aws s3 cp `
    $WheelPath.FullName `
    "s3://$BucketName/$GlueWheelKey" `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion

if ($LASTEXITCODE -ne 0) {
    throw "Failed to upload application wheel."
}

Write-Host "Deployment artifacts uploaded."

Write-Host ""
Write-Host "Creating local Glue IAM role..."

$TrustPolicyPath = Join-Path $env:TEMP "b2b-glue-trust-policy.json"
$S3PolicyPath = Join-Path $env:TEMP "b2b-glue-s3-policy.json"

@"
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
"@ | Set-Content -Path $TrustPolicyPath -Encoding utf8

@"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::$BucketName"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::$BucketName/*"
    }
  ]
}
"@ | Set-Content -Path $S3PolicyPath -Encoding utf8

aws iam create-role `
    --role-name $GlueRoleName `
    --assume-role-policy-document "file://$TrustPolicyPath" `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion *> $null

if ($LASTEXITCODE -ne 0) {
    throw "Failed to create Glue IAM role '$GlueRoleName'."
}

aws iam put-role-policy `
    --role-name $GlueRoleName `
    --policy-name "GlueS3Access" `
    --policy-document "file://$S3PolicyPath" `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion *> $null

if ($LASTEXITCODE -ne 0) {
    throw "Failed to attach S3 policy to Glue IAM role."
}

Write-Host "Glue IAM role created."

$CreatedGlueRoleArn = aws iam get-role `
    --role-name $GlueRoleName `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion `
    --query "Role.Arn" `
    --output text

if ($LASTEXITCODE -ne 0 -or -not $CreatedGlueRoleArn) {
    throw "Failed to verify Glue IAM role."
}

if ($CreatedGlueRoleArn -ne $GlueRoleArn) {
    throw "Unexpected Glue IAM role ARN: $CreatedGlueRoleArn"
}

Write-Host "Glue IAM role verified."

Write-Host ""
Write-Host "Creating local Glue job..."

$GlueCommandPath = Join-Path $env:TEMP "b2b-glue-command.json"
$GlueDefaultArgumentsPath = Join-Path $env:TEMP "b2b-glue-default-arguments.json"

@"
{
  "Name": "glueetl",
  "ScriptLocation": "$GlueScriptUri",
  "PythonVersion": "3"
}
"@ | Set-Content -Path $GlueCommandPath -Encoding utf8

@"
{
  "--job-language": "python",
  "--additional-python-modules": "$GlueWheelUri"
}
"@ | Set-Content -Path $GlueDefaultArgumentsPath -Encoding utf8

aws glue create-job `
    --name $GlueJobName `
    --role $GlueRoleArn `
    --command "file://$GlueCommandPath" `
    --glue-version $GlueVersion `
    --worker-type "G.1X" `
    --number-of-workers 2 `
    --default-arguments "file://$GlueDefaultArgumentsPath" `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion *> $null

if ($LASTEXITCODE -ne 0) {
    throw "Failed to create local Glue job '$GlueJobName'."
}

Write-Host "Local Glue job created."

Write-Host ""
Write-Host "Verifying local Glue job..."

$CreatedGlueJob = aws glue get-job `
    --job-name $GlueJobName `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion `
    --query "Job" `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0 -or -not $CreatedGlueJob) {
    throw "Failed to verify local Glue job."
}

if ($CreatedGlueJob.GlueVersion -ne $GlueVersion) {
    throw "Unexpected Glue version: $($CreatedGlueJob.GlueVersion)"
}

if ($CreatedGlueJob.Command.ScriptLocation -ne $GlueScriptUri) {
    throw "Unexpected Glue script location: $($CreatedGlueJob.Command.ScriptLocation)"
}

if ($CreatedGlueJob.DefaultArguments.'--additional-python-modules' -ne $GlueWheelUri) {
    throw "Unexpected Glue wheel URI."
}

Write-Host "Local Glue job verified."

Write-Host ""
Write-Host "Local deployment completed successfully."
