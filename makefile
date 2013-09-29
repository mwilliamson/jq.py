.PHONY: test upload clean bootstrap setup

test:
	_virtualenv/bin/nosetests tests

test-all: setup
	_virtualenv/bin/tox
	make clean
	
upload: setup
	python setup.py sdist upload
	make clean
	
register: setup
	python setup.py register

README:
	pandoc --from=markdown --to=rst README.md > README

clean:
	rm -f README
	rm -f MANIFEST
	rm -rf dist
	
bootstrap: _virtualenv jq.c setup
	_virtualenv/bin/pip install -e .
ifneq ($(wildcard test-requirements.txt),) 
	_virtualenv/bin/pip install -r test-requirements.txt
endif
	make clean

setup: README

_virtualenv: 
	virtualenv _virtualenv

jq.c: _virtualenv
	_virtualenv/bin/pip install cython
	_virtualenv/bin/cython jq.pyx
