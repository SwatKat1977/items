SET PYTHONPATH=.;unit_tests/shared

python -m coverage run --rcfile=.github/workflows/.coveragerc_shared -m unittest -v unit_tests/shared/main.py
python -m coverage report -m