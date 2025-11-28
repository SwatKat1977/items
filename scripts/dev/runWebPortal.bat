@echo off
set PYTHONPATH=services/web_portal_svc;items/shared;common
set QUART_APP=services/web_portal_svc
set QUART_DEBUG=1
set ITEMS_WEB_PORTAL_SVC_CONFIG_FILE_REQUIRED=0
set LOGGING_LOG_LEVEL=DEBUG
quart run -p 8181
