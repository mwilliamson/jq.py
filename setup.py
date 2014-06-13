#!/usr/bin/env python

import os
import subprocess
from setuptools import setup
from distutils.extension import Extension
from distutils.command.build_ext import build_ext


def path_in_dir(relative_path):
    return os.path.join(os.path.dirname(__file__), relative_path)

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


jq_lib_dir = path_in_dir("_jq-lib")

class jq_build_ext(build_ext):
    def run(self):
        
        def command(args):
            subprocess.check_call(args, cwd=path_in_dir(jq_lib_dir))
            
        if os.path.exists(jq_lib_dir):
            command(["git", "fetch"])
            command(["git", "checkout", "jq-1.4"])
        else:    
            subprocess.check_call([
                "git", "clone",
                "https://github.com/stedolan/jq.git",
                jq_lib_dir
            ])
            command(["git", "checkout", "jq-1.4"])
        
        command(["mkdir", "-p", "m4"])
        command(["autoreconf", "-i"])
        command(["./configure", "CFLAGS=-fPIC"])
        command(["make", "clean"])
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
    version='0.1.0',
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

