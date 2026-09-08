#!/usr/bin/env bash

set -euo pipefail

MINISTACK_CONTAINER="b2b-ministack"

echo "B2B ERP Data Integrator - Stop local environment"

echo
echo "Checking Docker..."

if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running." >&2
    exit 1
fi

echo "Docker is running."

echo
echo "Stopping MiniStack..."

if ! docker container inspect "$MINISTACK_CONTAINER" >/dev/null 2>&1; then
    echo "MiniStack container does not exist. Nothing to stop."

    echo
    echo "Local environment stopped successfully."
    exit 0
fi

RUNNING="$(
    docker inspect \
        --format '{{.State.Running}}' \
        "$MINISTACK_CONTAINER"
)"

if [[ "$RUNNING" == "true" ]]; then
    if ! docker stop "$MINISTACK_CONTAINER" >/dev/null; then
        echo "Failed to stop MiniStack container." >&2
        exit 1
    fi

    echo "MiniStack stopped."
else
    echo "MiniStack is already stopped."
fi

echo
echo "Local environment stopped successfully."
