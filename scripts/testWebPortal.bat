rem @echo off
SET PYTHONPATH=items/shared;services/web_portal_svc;unit_tests/web_portal_svc;common
python -m coverage run --rcfile=.github/workflows/.coveragerc_web_portal_svc -m unittest -v unit_tests/web_portal_svc/main.py
python -m coverage report -m