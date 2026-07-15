export PYTHONPATH=items/shared:unit_tests/cms_svc:services/cms_svc
export ITEMS_CMS_SVC_CONFIG_FILE=

coverage run --rcfile=.github/workflows/.coveragerc_cms_svc -m unittest -v unit_tests/cms_svc/main.py
coverage report -m
