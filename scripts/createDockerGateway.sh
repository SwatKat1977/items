#!/usr/bin/env bash

set -euo pipefail

usage() {
    echo "Usage: $0 <tag>"
    echo
    echo "Example:"
    echo "  $0 latest"
    echo "  $0 1.0.0"
    exit 1
}

if [ $# -ne 1 ]; then
    usage
fi

TAG="$1"

echo "Building Docker image items_cms:${TAG}..."

docker build \
    -f docker/Dockerfile.gateway_svc \
    -t "items_gateway:${TAG}" \
    .

echo
echo "Successfully built items_gateway:${TAG}"