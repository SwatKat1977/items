export PYTHONPATH=.
export QUART_APP=items/services/items_cms
export ITEMS_CMS_CONFIG_FILE_REQUIRED=0
export ITEMS_CMS_CONFIG_FILE=cms.cfg
export LOGGING_LOG_LEVEL=DEBUG

python -m items.services.items_cms.run
