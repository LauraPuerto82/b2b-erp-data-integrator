#requires -Version 7.0

$ErrorActionPreference = "Stop"

$MiniStackContainer = "b2b-ministack"

Write-Host "B2B ERP Data Integrator - Stop local environment"

Write-Host ""
Write-Host "Checking Docker..."

try {
    docker info *> $null
} catch {
    throw "Docker is not running."
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "MiniStack container does not exist. Nothing to stop."

    Write-Host ""
    Write-Host "Local environment stopped successfully."
    exit 0
}

Write-Host "Docker is running."

Write-Host ""
Write-Host "Stopping MiniStack..."

$ContainerExists = docker container inspect $MiniStackContainer 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "MiniStack container does not exist. Nothing to stop."
    exit 0
}

$Running = docker inspect `
    --format "{{.State.Running}}" `
    $MiniStackContainer

if ($LASTEXITCODE -ne 0) {
    throw "Failed to inspect MiniStack container."
}

if ($Running -eq "true") {
    docker stop $MiniStackContainer *> $null

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to stop MiniStack container."
    }

    Write-Host "MiniStack stopped."
} else {
    Write-Host "MiniStack is already stopped."
}

Write-Host ""
Write-Host "Local environment stopped successfully."
