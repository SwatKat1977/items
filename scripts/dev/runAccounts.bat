@echo off
set PYTHONPATH=services/accounts_svc;items/shared;common
set QUART_APP=services/accounts_svc
set QUART_DEBUG=1
set ITEMS_ACCOUNTS_SVC_CONFIG_FILE_REQUIRED=0
set LOGGING_LOG_LEVEL=DEBUG
set BACKEND_DB_FILENAME=databases/items_accounts_svc.db
rem source .venv/bin/activate
quart run -p 4000
