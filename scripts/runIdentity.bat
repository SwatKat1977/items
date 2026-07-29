@echo off
echo Starting ITEMS - Identity Service
set PYTHONPATH=.
set QUART_APP=items/services/items_identity
rem set ITEMS_IDENTITY_CONFIG_FILE_REQUIRED=1
rem set ITEMS_IDENTITY_CONFIG_FILE=configs/svc.cfg
set BACKEND_DB_FILENAME=databases/items_identity.LATEST.db
set LOGGING_LOG_LEVEL=DEBUG

python -m items.services.items_identity.run