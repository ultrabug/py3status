qa:
	hatch run style:format
	hatch run style:check

clean:
	hatch clean

release: clean qa test build
	hatch publish -u __token__

serve:
	mkdocs serve

build:
	hatch build

# TODO: maybe move the docs to github
#deploy: qa test
#	mkdocs gh-deploy

test:
	hatch run all
