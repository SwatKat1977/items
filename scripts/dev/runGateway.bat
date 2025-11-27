@echo off
SET PYTHONPATH=items/gateway_svc;items/shared;
SET QUART_APP=items/gateway_svc
SET ITEMS_GATEWAY_SVC_CONFIG_FILE=configs/gateway.cfg
SET ITEMS_GATEWAY_SVC_CONFIG_FILE_REQUIRED=1
SET GENERAL_API_SIGNING_SECRET=ApiSigningSecret
SET GENERAL_METADATA_CONFIG_FILE=configs/metadata.config
SET APIS_ACCOUNTS_SVC=http://localhost:4000/
SET APIS_CMS_SVC=http://localhost:5050/

python -m quart run -p 3000