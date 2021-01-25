.PHONY: test test-all upload register clean bootstrap

test: bootstrap
	_virtualenv/bin/nosetests tests

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
	python3 -m venv _virtualenv
	_virtualenv/bin/pip install --upgrade pip
	_virtualenv/bin/pip install --upgrade setuptools
	_virtualenv/bin/pip install --upgrade wheel

jq.c: _virtualenv jq.pyx
	_virtualenv/bin/pip install cython==0.29.16
	_virtualenv/bin/cython jq.pyx
