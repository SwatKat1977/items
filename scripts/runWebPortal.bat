@echo off
SET PYTHONPATH=.
SET QUART_APP=items/services/items_web_portal
set QUART_DEBUG=1
set ITEMS_WEB_PORTAL_SVC_CONFIG_FILE_REQUIRED=0
set LOGGING_LOG_LEVEL=DEBUG

python -m items.services.items_web_portal.run
