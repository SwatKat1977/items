@echo off
set PYTHONPATH=services/cms_svc;items/shared;common
set QUART_APP=services/cms_svc
set ITEMS_CMS_SVC_CONFIG_FILE_REQUIRED=1
set ITEMS_CMS_SVC_CONFIG_FILE=configs/cms.cfg
set BACKEND_DB_FILENAME=databases/items_cms_svc.LATEST.db
set LOGGING_LOG_LEVEL=DEBUG

quart run -p 5050 --reload
