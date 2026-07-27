#!/usr/bin/env bash

set -euo pipefail

usage() {
    echo "Usage: $0 <config-file> <db-file> <tag>"
    exit 1
}

if [ $# -ne 3 ]; then
    usage
fi

CONFIG_FILE="$(realpath "$1")"
DB_FILE="$(realpath "$2")"
IMAGE_TAG="$3"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found:"
    echo "  $CONFIG_FILE"
    exit 1
fi

echo "Running items_identity:${IMAGE_TAG}"
echo "Using config: ${CONFIG_FILE}"

NETWORK_NAME="items-net"

if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    echo "Creating Docker network '$NETWORK_NAME'..."
    docker network create "$NETWORK_NAME"
fi

docker run \
    --rm \
    -p 5050:5050 \
    --name items-identity \
    --network "${NETWORK_NAME}" \
    -v "${CONFIG_FILE}:/usr/local/items/identity.cfg:ro" \
    -v "${DB_FILE}:/usr/local/items/identity.db" \
    -d \
    "items_identity:${IMAGE_TAG}"
