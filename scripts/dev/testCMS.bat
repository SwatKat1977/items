set PYTHONPATH=unit_tests/items_cms
set ITEMS_CMS_SVC_CONFIG_FILE=

coverage run --rcfile=.github/workflows/.coveragerc_cms_svc -m unittest -v unit_tests/items_cms/main.py
coverage report -m
