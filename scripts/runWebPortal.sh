export PYTHONPATH=.
export QUART_APP=items/services/items_web_portal
export QUART_DEBUG=1
export ITEMS_WEB_PORTAL_SVC_CONFIG_FILE_REQUIRED=0
export LOGGING_LOG_LEVEL=DEBUG

python -m items.services.items_web_portal.run
