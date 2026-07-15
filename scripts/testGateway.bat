@echo off
SET ITEMS_ACCOUNTS_SVC_CONFIG_FILE_REQUIRED=
SET ITEMS_GATEWAY_SVC_CONFIG_FILE=
SET ITEMS_GATEWAY_SVC_CONFIG_FILE_REQUIRED=

SET PYTHONPATH=items/shared;services/gateway_svc;unit_tests/items_gateway
coverage run --rcfile=.github/workflows/.coveragerc_gateway_svc -m unittest -v unit_tests/items_gateway/main.py
coverage report -m
