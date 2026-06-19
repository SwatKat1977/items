@echo off
echo Starting ITEMS - Identity Service
set PYTHONPATH=.
set QUART_APP=items/services/items_identity
rem set ITEMS_IDENTITY_CONFIG_FILE_REQUIRED=1
rem set ITEMS_IDENTITY_CONFIG_FILE=configs/svc.cfg
rem set BACKEND_DB_FILENAME=databases/items_accounts_svc.db
set LOGGING_LOG_LEVEL=DEBUG

python -m items.services.items_identity.run