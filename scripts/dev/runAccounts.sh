export PYTHONPATH=items/accounts_svc:items/shared:common
export QUART_APP=items/accounts_svc
export QUART_DEBUG=1
export ITEMS_ACCOUNTS_SVC_CONFIG_FILE_REQUIRED=0
export LOGGING_LOG_LEVEL=DEBUG
export BACKEND_DB_FILENAME=databases/items_accounts_svc.db
quart run -p 4000
