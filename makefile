.PHONY: test upload clean bootstrap setup assert-converted-readme

test: bootstrap
	_virtualenv/bin/nosetests tests

test-all: setup
	_virtualenv/bin/tox
	make clean
	
upload: setup assert-converted-readme
	python setup.py sdist upload
	make clean
	
register: setup
	python setup.py register

README:
	pandoc --from=markdown --to=rst README.md > README || cp README.md README

assert-converted-readme:
	test "`cat README`" != "`cat README.md`"

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

jq.c: _virtualenv jq.pyx
	_virtualenv/bin/pip install cython
	_virtualenv/bin/cython jq.pyx
