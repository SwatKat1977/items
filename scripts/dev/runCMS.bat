@echo off
set PYTHONPATH=.
set QUART_APP=items/services/cms_svc
set ITEMS_CMS_SVC_CONFIG_FILE_REQUIRED=1
set ITEMS_CMS_SVC_CONFIG_FILE=configs/cms.cfg
set BACKEND_DB_FILENAME=databases/items_cms.LATEST.db
set LOGGING_LOG_LEVEL=DEBUG

python -m items.services.items_cms.run
