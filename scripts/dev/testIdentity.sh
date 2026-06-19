export PYTHONPATH=.:items/services/items_identity:unit_tests/identity_svc
export ITEMS_IDENTITY_CONFIG_FILE=

source venv/bin/activate
coverage run --rcfile=.github/workflows/.coveragerc_identity_svc -m unittest -v unit_tests/identity_svc/main.py
coverage report -m
