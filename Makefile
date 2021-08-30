qa:
	tox

clean:
	rm -rf dist

release: clean qa test
	python3 setup.py sdist && python3 -m twine upload dist/*

serve:
	mkdocs serve

build:
	mkdocs build

# TODO: maybe move the docs to github
#deploy: qa test
#	mkdocs gh-deploy

test:
	pytest -xsvv
