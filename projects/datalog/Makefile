.PHONY: test

deploy: .dev
	source .dev/bin/activate; pip install twine; rm -r dist; python setup.py sdist; twine upload dist/*;

.dev:
	virtualenv --python=`which python3` .dev
	source .dev/bin/activate; pip install pytest; python setup.py develop

node_modules/canopy:
	npm install canopy

src/python/datalog/parser.py: node_modules/canopy src/datalog.peg
	node_modules/canopy/bin/canopy --lang=python src/datalog.peg
	mv src/datalog.py src/python/datalog/parser.py

test: .dev $(wildcard src/**/*) $(wildcard test/**/*)
	source .dev/bin/activate; PYTHONPATH=".:src/" pytest -vv
