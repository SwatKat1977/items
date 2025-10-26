export PYTHONPATH=services/accounts_svc:items/shared:common:unit_tests/accounts_svc

coverage run --rcfile=.github/workflows/.coveragerc_accounts_svc -m unittest -v unit_tests/accounts_svc/main.py
coverage report -m
