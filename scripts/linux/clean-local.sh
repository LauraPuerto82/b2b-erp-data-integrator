#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

MINISTACK_CONTAINER="b2b-ministack"

echo "B2B ERP Data Integrator - Clean local environment"

echo
echo "Checking Docker..."

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running." >&2
    exit 1
fi

echo "Docker is running."

echo
echo "Removing MiniStack container..."

if docker container inspect "$MINISTACK_CONTAINER" >/dev/null 2>&1; then
    if ! docker rm -f "$MINISTACK_CONTAINER" >/dev/null; then
        echo "Failed to remove MiniStack container." >&2
        exit 1
    fi

    echo "MiniStack container removed."
else
    echo "MiniStack container does not exist."
fi

echo
echo "Removing residual Glue containers..."

GLUE_CONTAINERS="$(
    docker ps -a \
        --filter "name=ministack-glue-" \
        --format '{{.Names}}'
)"

if [[ -n "$GLUE_CONTAINERS" ]]; then
    while IFS= read -r container; do
        [[ -z "$container" ]] && continue

        if ! docker rm -f "$container" >/dev/null; then
            echo "Failed to remove Glue container: $container" >&2
            exit 1
        fi

        echo "Removed Glue container: $container"
    done <<< "$GLUE_CONTAINERS"
else
    echo "No residual Glue containers found."
fi

echo
echo "Removing build artifacts..."

DIST_PATH="$PROJECT_ROOT/dist"

if [[ -d "$DIST_PATH" ]]; then
    rm -rf "$DIST_PATH"
    echo "Removed dist directory."
else
    echo "dist directory does not exist."
fi

echo
echo "Removing temporary deployment files..."

rm -f /tmp/b2b-glue-*.json 2>/dev/null || true
rm -rf /tmp/b2b-erp-data-integrator-e2e 2>/dev/null || true

echo "Temporary deployment files removed."

echo
echo "Local environment cleaned successfully."
