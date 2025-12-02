@echo off
SET ITEMS_ACCOUNTS_SVC_CONFIG_FILE_REQUIRED=1
SET ITEMS_ACCOUNTS_SVC_CONFIG_FILE=
SET PYTHONPATH=./shared;./gateway_svc;./unittests_gateway_svc
coverage run --rcfile=coverage_gateway_svc.cfg -m unittest -v unittests_gateway_svc/main.py
coverage report -m
