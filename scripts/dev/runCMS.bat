@echo off
set PYTHONPATH=services/cms_svc;items/shared
set QUART_APP=services/cms_svc
set ITEMS_CMS_SVC_CONFIG_FILE_REQUIRED=0
set ITEMS_CMS_SVC_CONFIG_FILE=cms.cfg
set LOGGING_LOG_LEVEL=DEBUG

quart run -p 5050 --reload
