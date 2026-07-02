@echo off
SET PYTHONPATH=.
SET QUART_APP=items/services/items_gateway
SET QUART_DEBUG=1
SET ITEMS_GATEWAY_SVC_CONFIG_FILE=configs/gateway.cfg
SET ITEMS_GATEWAY_SVC_CONFIG_FILE_REQUIRED=1
SET GENERAL_API_SIGNING_SECRET=ApiSigningSecret
SET GENERAL_METADATA_CONFIG_FILE=configs/metadata.config
@rem SET APIS_CMS_SVC=http://localhost:5050/
set LOGGING_LOG_LEVEL=DEBUG

python -m items.services.items_gateway.run
