export PYTHONPATH=.
export QUART_APP=items/services/items_identity
export QUART_DEBUG=1
#export ITEMS_ACCOUNTS_SVC_CONFIG_FILE_REQUIRED=0
export LOGGING_LOG_LEVEL=DEBUG
export BACKEND_DB_FILENAME=databases/items_accounts_svc.db

python -m items.services.items_identity.run