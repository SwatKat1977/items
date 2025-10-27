export PYTHONPATH=services/accounts_svc:items/shared:common
export QUART_APP=services/accounts_svc
export QUART_DEBUG=1
export ITEMS_ACCOUNTS_SVC_CONFIG_FILE_REQUIRED=0
export LOGGING_LOG_LEVEL=DEBUG
export BACKEND_DB_FILENAME=databases/items_accounts_svc.db
source .venv/bin/activate
$VIRTUAL_ENV/bin/quart run -p 4000
