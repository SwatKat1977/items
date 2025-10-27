export PYTHONPATH=items/cms_svc:items/shared
export QUART_APP=items/cms_svc
export ITEMS_CMS_SVC_CONFIG_FILE_REQUIRED=0
export ITEMS_CMS_SVC_CONFIG_FILE=cms.cfg
export LOGGING_LOG_LEVEL=DEBUG

quart run -p 5050 --reload
