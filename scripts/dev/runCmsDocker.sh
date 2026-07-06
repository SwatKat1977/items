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
DB_DIR="$(dirname "$DB_FILE")"
DB_BASENAME="$(basename "$DB_FILE")"
IMAGE_TAG="$3"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found:"
    echo "  $CONFIG_FILE"
    exit 1
fi

if [ ! -f "$DB_FILE" ]; then
    echo "Error: Database file not found:"
    echo "  $DB_FILE"
    exit 1
fi

echo "Running items_cms:${IMAGE_TAG}"
echo "Using config: ${CONFIG_FILE}"
echo "Using database: ${DB_FILE}"

NETWORK_NAME="items-net"

if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    echo "Creating Docker network '$NETWORK_NAME'..."
    docker network create "$NETWORK_NAME"
fi

docker run \
    --rm \
    -p 6050:6050 \
    --name items-cms \
    --network "${NETWORK_NAME}" \
    --user "$(id -u):$(id -g)" \
    -v "${CONFIG_FILE}:/usr/local/items/cms.cfg:ro" \
    -v "${DB_DIR}:/usr/local/items/data" \
    -e "BACKEND_DB_FILENAME=/usr/local/items/data/${DB_BASENAME}" \
    -d \
    "items_cms:${IMAGE_TAG}"