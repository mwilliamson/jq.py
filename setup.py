#!/usr/bin/env python

import os
from setuptools import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

jq_extension = Extension(
    "jq",
    sources=["jq.pyx"],
    include_dirs=["../jq/"],
    libraries=["jq"],
    library_dirs=["../jq/"],
)

setup(
    name='jq',
    version='0.1.0',
    description='jq is a lightweight and flexible command-line JSON processor.',
    long_description=read("README"),
    author='Michael Williamson',
    url='http://github.com/mwilliamson/jq.py',
    cmdclass={"build_ext": build_ext},
    ext_modules = [jq_extension]
)

