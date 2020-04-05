#
# Updated cython version to 0.29.16, the make was failing
# using the version it was previously pinned on, even on
# x86_64
#
.PHONY: test test-all upload register clean bootstrap

test: bootstrap
	_virtualenv/bin/nosetests tests

upload: jq.c
	python setup.py sdist upload
	make clean

register:
	python setup.py register

clean:
	rm -f MANIFEST *gz
	rm -rf dist jq-jq-* *.egg-info

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
	_virtualenv/bin/pip install cython==0.29.16
	_virtualenv/bin/cython jq.pyx
