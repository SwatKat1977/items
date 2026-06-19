export PYTHONPATH=.:items/services/items_identity:unit_tests/items_identity
export ITEMS_IDENTITY_CONFIG_FILE=

source venv/bin/activate
coverage run --rcfile=.github/workflows/.coveragerc_identity_svc -m unittest -v unit_tests/items_identity/main.py
coverage report -m
