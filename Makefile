qa:
	isort --profile black . && black . && flake8

clean:
	rm -rf dist

release: clean qa test
	python3 setup.py sdist && python3 -m twine upload dist/*

serve:
	mkdocs serve

build:
	mkdocs build

deploy: qa test
	mkdocs gh-deploy

test:
	pytest -xsvv
