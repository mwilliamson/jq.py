#!/usr/bin/env python

import os
import subprocess
import tarfile
import shutil

from setuptools import setup
from distutils.extension import Extension
from distutils.command.build_ext import build_ext

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

def path_in_dir(relative_path):
    return os.path.join(os.path.dirname(__file__), relative_path)

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


tarball_path = path_in_dir("_jq-lib-1.4.tar.gz")
jq_lib_dir = path_in_dir("jq-jq-1.4")

class jq_build_ext(build_ext):
    def run(self):
        if os.path.exists(tarball_path):
            os.unlink(tarball_path)
        urlretrieve("https://github.com/stedolan/jq/archive/jq-1.4.tar.gz", tarball_path)
        
        if os.path.exists(jq_lib_dir):
            shutil.rmtree(jq_lib_dir)
        tarfile.open(tarball_path, "r:gz").extractall(path_in_dir("."))
        
        def command(args):
            subprocess.check_call(args, cwd=jq_lib_dir)
        
        command(["autoreconf", "-i"])
        command(["./configure", "CFLAGS=-fPIC"])
        command(["make"])
        
        build_ext.run(self)


jq_extension = Extension(
    "jq",
    sources=["jq.c"],
    include_dirs=[jq_lib_dir],
    #libraries=["jq"],
    extra_objects=[os.path.join(jq_lib_dir, ".libs/libjq.a")],
    #library_dirs=[os.path.join(jq_lib_dir, ".libs")],
)

setup(
    name='jq',
    version='0.1.1',
    description='jq is a lightweight and flexible JSON processor.',
    long_description=read("README.rst"),
    author='Michael Williamson',
    url='http://github.com/mwilliamson/jq.py',
    license='BSD 2-Clause',
    ext_modules = [jq_extension],
    cmdclass={"build_ext": jq_build_ext},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)

