#!/usr/bin/env bash

export PYTHONPATH=.
export QUART_APP=items/services/items_gateway
export QUART_DEBUG=1
export ITEMS_GATEWAY_CONFIG_FILE=configs/gateway.cfg
export ITEMS_GATEWAY_CONFIG_FILE_REQUIRED=1
#export GENERAL_API_SIGNING_SECRET=ApiSigningSecret
export GENERAL_METADATA_CONFIG_FILE=configs/metadata.config
# export APIS_CMS_SVC=http://localhost:5050/
export LOGGING_LOG_LEVEL=DEBUG

python -m items.services.items_gateway.run
