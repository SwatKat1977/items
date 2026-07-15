#!/usr/bin/env bash

set -euo pipefail

usage() {
    echo "Usage: $0 <config-file> <tag>"
    exit 1
}

if [ $# -ne 2 ]; then
    usage
fi

CONFIG_FILE="$(realpath "$1")"
IMAGE_TAG="$2"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found:"
    echo "  $CONFIG_FILE"
    exit 1
fi

echo "Running items_gateway:${IMAGE_TAG}"
echo "Using config: ${CONFIG_FILE}"

NETWORK_NAME="items-net"

if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    echo "Creating Docker network '$NETWORK_NAME'..."
    docker network create "$NETWORK_NAME"
fi

docker run \
    --rm \
    -p 7050:7050 \
    --name items-gateway \
    --network "${NETWORK_NAME}" \
    -v "${CONFIG_FILE}:/usr/local/items/gateway.cfg:ro" \
    "items_gateway:${IMAGE_TAG}"