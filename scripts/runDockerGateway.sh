#!/usr/bin/env bash

set -euo pipefail

usage() {
    echo "Usage: $0 <config-file> <secret> <metadata_file> <tag>"
    exit 1
}

if [ $# -ne 4 ]; then
    usage
fi

CONFIG_FILE="$(realpath "$1")"
API_SECRET="$2"
METADATA_FILE="$(realpath "$3")"
IMAGE_TAG="$4"

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
    -e GENERAL_API_SIGNING_SECRET="{API_SECRET}" \
    -v "${CONFIG_FILE}:/usr/local/items/gateway.cfg:ro" \
    -v "${METADATA_FILE}:/usr/local/items/metadata.config" \
    "items_gateway:${IMAGE_TAG}"
