export PYTHONPATH=.
export QUART_APP=items/services/items_cms
export ITEMS_CMS_CONFIG_FILE_REQUIRED=1
export ITEMS_CMS_CONFIG_FILE=configs/cms.cfg
export LOGGING_LOG_LEVEL=DEBUG
export BACKEND_DB_FILENAME=databases/items_cms.LATEST.db

python -m items.services.items_cms.run
