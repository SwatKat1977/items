set PYTHONPATH=.;items/services/items_identity;unit_tests/items_identity
set ITEMS_IDENTITY_CONFIG_FILE=

python -m coverage run --rcfile=.github/workflows/.coveragerc_identity_svc -m unittest -v unit_tests/items_identity/main.py
python -m coverage report -m
