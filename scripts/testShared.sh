export PYTHONPATH=items/shared:unit_tests/shared

coverage run --rcfile=.github/workflows/.coveragerc_shared -m unittest -v unit_tests/shared/main.py
coverage report -m