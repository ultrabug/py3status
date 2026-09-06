qa:
	hatch run style:format
	hatch run style:check

clean:
	hatch clean

release: clean qa test build
	hatch publish -u __token__

serve:
	hatch -e docs run serve

build:
	hatch build

test:
	hatch run all
