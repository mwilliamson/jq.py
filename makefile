.PHONY: test test-all upload register clean bootstrap

test: bootstrap
	_virtualenv/bin/nosetests tests

test-all:
	_virtualenv/bin/tox
	make clean
	
upload: jq.c
	python setup.py sdist upload
	make clean
	
register:
	python setup.py register

clean:
	rm -f MANIFEST
	rm -rf dist
	
bootstrap: _virtualenv jq.c
	_virtualenv/bin/pip install -e .
ifneq ($(wildcard test-requirements.txt),) 
	_virtualenv/bin/pip install -r test-requirements.txt
endif
	make clean

_virtualenv: 
	virtualenv _virtualenv
	_virtualenv/bin/pip install --upgrade pip
	_virtualenv/bin/pip install --upgrade setuptools

jq.c: _virtualenv jq.pyx
	_virtualenv/bin/pip install cython==0.19.2
	_virtualenv/bin/cython jq.pyx
