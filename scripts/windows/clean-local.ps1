#requires -Version 7.0

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$MiniStackContainer = "b2b-ministack"

Write-Host "B2B ERP Data Integrator - Clean local environment"

Write-Host ""
Write-Host "Checking Docker..."

docker info *> $null

if ($LASTEXITCODE -ne 0) {
    throw "Docker is not running."
}

Write-Host "Docker is running."

Write-Host ""
Write-Host "Removing MiniStack container..."

docker container inspect $MiniStackContainer *> $null

if ($LASTEXITCODE -eq 0) {
    docker rm -f $MiniStackContainer *> $null

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to remove MiniStack container."
    }

    Write-Host "MiniStack container removed."
} else {
    Write-Host "MiniStack container does not exist."
}

Write-Host ""
Write-Host "Removing residual Glue containers..."

$GlueContainers = docker ps -a `
    --filter "name=ministack-glue-" `
    --format "{{.Names}}"

if ($GlueContainers) {
    foreach ($Container in $GlueContainers) {
        docker rm -f $Container *> $null

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to remove Glue container '$Container'."
        }

        Write-Host "Removed Glue container: $Container"
    }
} else {
    Write-Host "No residual Glue containers found."
}

Write-Host ""
Write-Host "Removing build artifacts..."

$DistPath = Join-Path $ProjectRoot "dist"

if (Test-Path $DistPath) {
    Remove-Item -Recurse -Force $DistPath
    Write-Host "Removed dist directory."
} else {
    Write-Host "dist directory does not exist."
}

Write-Host ""
Write-Host "Removing temporary deployment files..."

Get-ChildItem `
    -Path $env:TEMP `
    -Filter "b2b-glue-*.json" `
    -ErrorAction SilentlyContinue |
    Remove-Item -Force

$E2ETempDirectory = Join-Path $env:TEMP "b2b-erp-data-integrator-e2e"

if (Test-Path $E2ETempDirectory) {
    Remove-Item -Recurse -Force $E2ETempDirectory
}

Write-Host "Temporary deployment files removed."

Write-Host ""
Write-Host "Local environment cleaned successfully."
