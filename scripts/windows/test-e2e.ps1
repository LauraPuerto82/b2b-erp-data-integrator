$ErrorActionPreference = "Stop"

$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDirectory "..\..")

$AwsEndpoint = "http://localhost:4566"
$AwsRegion = "us-east-1"

$BucketName = "b2b-erp-data-integrator-local"
$GlueJobName = "b2b-erp-data-integrator-customers"

$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
$env:AWS_DEFAULT_REGION = $AwsRegion

Write-Host "B2B ERP Data Integrator - End-to-end test"
Write-Host "Project root: $ProjectRoot"

Write-Host ""
Write-Host "Checking local deployment..."

aws s3api head-bucket `
    --bucket $BucketName `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion *> $null

if ($LASTEXITCODE -ne 0) {
    throw "Local S3 bucket '$BucketName' was not found. Run deploy-local.ps1 first."
}

aws glue get-job `
    --job-name $GlueJobName `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion *> $null

if ($LASTEXITCODE -ne 0) {
    throw "Local Glue job '$GlueJobName' was not found. Run deploy-local.ps1 first."
}

Write-Host "Local deployment is available."

$DemoCsvPath = Join-Path $ProjectRoot "demo\erp_b_customers.csv"

if (-not (Test-Path $DemoCsvPath)) {
    throw "E2E demo CSV was not found: $DemoCsvPath"
}

$InputKey = "raw/erp_b/customers.csv"
$InputUri = "s3a://$BucketName/$InputKey"

$ProcessedUri = "s3a://$BucketName/processed/erp_b/"
$RejectedUri = "s3a://$BucketName/rejected/erp_b/"

Write-Host ""
Write-Host "Uploading E2E input dataset..."

aws s3 cp `
    $DemoCsvPath `
    "s3://$BucketName/$InputKey" `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion *> $null

if ($LASTEXITCODE -ne 0) {
    throw "Failed to upload E2E input dataset."
}

Write-Host "E2E input dataset uploaded."

$JobArgumentsPath = Join-Path $env:TEMP "b2b-glue-e2e-arguments.json"

@"
{
  "--JOB_NAME": "$GlueJobName",
  "--source_system": "ERP_B",
  "--input_path": "$InputUri",
  "--processed_path": "$ProcessedUri",
  "--rejected_path": "$RejectedUri"
}
"@ | Set-Content -Path $JobArgumentsPath -Encoding utf8

Write-Host ""
Write-Host "Starting Glue job..."

$JobRunId = aws glue start-job-run `
    --job-name $GlueJobName `
    --arguments "file://$JobArgumentsPath" `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion `
    --query "JobRunId" `
    --output text

if ($LASTEXITCODE -ne 0 -or -not $JobRunId) {
    throw "Failed to start Glue job."
}

Write-Host "Glue job started: $JobRunId"

Write-Host ""
Write-Host "Waiting for Glue job to finish..."

$MaxAttempts = 60
$Attempt = 0
$JobRunState = $null

do {
    $Attempt++

    $JobRunState = aws glue get-job-run `
        --job-name $GlueJobName `
        --run-id $JobRunId `
        --endpoint-url $AwsEndpoint `
        --region $AwsRegion `
        --query "JobRun.JobRunState" `
        --output text

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to query Glue job run '$JobRunId'."
    }

    if ($JobRunState -eq "SUCCEEDED") {
        break
    }

    if ($JobRunState -in @("FAILED", "STOPPED", "TIMEOUT", "ERROR")) {
        $ErrorMessage = aws glue get-job-run `
            --job-name $GlueJobName `
            --run-id $JobRunId `
            --endpoint-url $AwsEndpoint `
            --region $AwsRegion `
            --query "JobRun.ErrorMessage" `
            --output text

        throw "Glue job failed with state '$JobRunState'. $ErrorMessage"
    }

    Start-Sleep -Seconds 2
} while ($Attempt -lt $MaxAttempts)

if ($JobRunState -ne "SUCCEEDED") {
    throw "Glue job did not complete successfully within $($MaxAttempts * 2) seconds."
}

Write-Host "Glue job succeeded."

Write-Host ""
Write-Host "Verifying E2E outputs..."

$ProcessedObjects = aws s3api list-objects-v2 `
    --bucket $BucketName `
    --prefix "processed/erp_b/" `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion `
    --query "Contents[?ends_with(Key, '.parquet')].Key" `
    --output text

if ($LASTEXITCODE -ne 0 -or -not $ProcessedObjects) {
    throw "No processed Parquet output was generated."
}

$RejectedObjects = aws s3api list-objects-v2 `
    --bucket $BucketName `
    --prefix "rejected/erp_b/" `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion `
    --query "Contents[?ends_with(Key, '.json')].Key" `
    --output text

if ($LASTEXITCODE -ne 0 -or -not $RejectedObjects) {
    throw "No rejected JSON output was generated."
}

Write-Host "Processed and rejected outputs were generated."

$E2ETempDirectory = Join-Path $env:TEMP "b2b-erp-data-integrator-e2e"

Remove-Item `
    -Recurse `
    -Force `
    $E2ETempDirectory `
    -ErrorAction SilentlyContinue

New-Item `
    -ItemType Directory `
    -Path $E2ETempDirectory `
    -Force *> $null

$ProcessedDirectory = Join-Path $E2ETempDirectory "processed"
$RejectedDirectory = Join-Path $E2ETempDirectory "rejected"

aws s3 cp `
    "s3://$BucketName/processed/erp_b/" `
    $ProcessedDirectory `
    --recursive `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion *> $null

if ($LASTEXITCODE -ne 0) {
    throw "Failed to download processed E2E output."
}

aws s3 cp `
    "s3://$BucketName/rejected/erp_b/" `
    $RejectedDirectory `
    --recursive `
    --endpoint-url $AwsEndpoint `
    --region $AwsRegion *> $null

if ($LASTEXITCODE -ne 0) {
    throw "Failed to download rejected E2E output."
}

Write-Host "Validating processed customer..."

$ProcessedValidation = uv run python -c @"
import json
import pathlib
import pyarrow.parquet as pq

directory = pathlib.Path(r"$ProcessedDirectory")
files = list(directory.glob("*.parquet"))

rows = []
for file in files:
    rows.extend(pq.read_table(file).to_pylist())

print(json.dumps(rows))
"@

if ($LASTEXITCODE -ne 0) {
    throw "Failed to read processed Parquet output."
}

$ProcessedCustomers = $ProcessedValidation | ConvertFrom-Json

if (@($ProcessedCustomers).Count -ne 1) {
    throw "Expected exactly 1 processed customer."
}

$ProcessedCustomer = @($ProcessedCustomers)[0]

if (
    $ProcessedCustomer.external_id -ne "C001" -or
    $ProcessedCustomer.name -ne "ACME S.L." -or
    $ProcessedCustomer.tax_id -ne "B12345678" -or
    $ProcessedCustomer.country -ne "ES" -or
    $ProcessedCustomer.email -ne "info@acme.es"
) {
    throw "Processed customer does not match the expected E2E result."
}

if (-not $ProcessedCustomer.customer_id) {
    throw "Processed customer does not contain a customer_id."
}

Write-Host "Processed customer is correct."

Write-Host "Validating rejected customer..."

$RejectedFiles = Get-ChildItem `
    -Path $RejectedDirectory `
    -Filter "*.json"

$RejectedCustomers = @(
    foreach ($File in $RejectedFiles) {
        Get-Content $File.FullName |
            ForEach-Object { $_ | ConvertFrom-Json }
    }
)

if ($RejectedCustomers.Count -ne 1) {
    throw "Expected exactly 1 rejected customer."
}

$RejectedCustomer = $RejectedCustomers[0]

if (
    $RejectedCustomer.external_id -ne "C002" -or
    $RejectedCustomer.name -ne "Globex S.L." -or
    $RejectedCustomer.tax_id -ne "B1234" -or
    $RejectedCustomer.country -ne "ES" -or
    $RejectedCustomer.email -ne "info@globex.es" -or
    $RejectedCustomer.reason -ne "Invalid tax ID"
) {
    throw "Rejected customer does not match the expected E2E result."
}

Write-Host "Rejected customer is correct."

Write-Host ""
Write-Host "E2E test passed successfully."
