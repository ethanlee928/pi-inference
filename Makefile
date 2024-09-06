.PHONY: style check_code_quality

export PYTHONPATH = .
check_dirs := pi_utils

style:
	black --config styles/black.toml $(check_dirs)
	isort --profile black $(check_dirs)

check_code_quality:
	make style
	# stop the build if there are Python syntax errors or undefined names
	flake8 $(check_dirs) --config styles/flake8.cfg --count --select=E9,F63,F7,F82 --show-source --statistics
	# exit-zero treats all errors as warnings. E203 for black, E501 for docstring, W503 for line breaks before logical operators 
	flake8 $(check_dirs) --config styles/flake8.cfg --count --max-line-length=88 --exit-zero  --ignore=D --extend-ignore=E203,E501,E402,W503  --statistics

publish:
	python setup.py sdist bdist_wheel
	twine upload -r testpypi dist/* -u ${PYPI_USERNAME} -p ${PYPI_TEST_PASSWORD} --verbose 
	twine check dist/*
	twine upload dist/* -u ${PYPI_USERNAME} -p ${PYPI_PASSWORD} --verbose

run-tests:
	python3 -m pytest tests/ -v
