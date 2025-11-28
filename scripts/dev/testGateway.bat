rem @echo off
SET PYTHONPATH=items/shared;items/gateway_svc;unit_tests/gateway_svc
coverage run --rcfile=.github/workflows/.coveragerc_gateway_svc -m unittest -v unit_tests/gateway_svc/main.py
coverage report -m