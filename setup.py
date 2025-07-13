#!/usr/bin/env python

import os
import shlex
import shutil
import subprocess
import sys
import sysconfig
import tarfile

from Cython.Build import cythonize
from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension


def _path_in_dir(relative_path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

def _dep_source_path(relative_path):
    return os.path.join(_path_in_dir("deps"), relative_path)

def _dep_build_path(relative_path):
    return os.path.join(_path_in_dir("_deps/build"), relative_path)

def _read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


jq_lib_tarball_path = _dep_source_path("jq-1.8.1.tar.gz")
jq_lib_dir = _dep_build_path("jq-1.8.1")

class jq_with_deps_build_ext(build_ext):
    def finalize_options(self):
        build_ext.finalize_options(self)
        if os.name == "nt":
            self.compiler = "mingw32"

    def run(self):
        if not os.path.exists(_dep_build_path(".")):
            os.makedirs(_dep_build_path("."))
        self._build_libjq()
        build_ext.run(self)

    def _build_libjq(self):
        self._build_lib(
            tarball_path=jq_lib_tarball_path,
            lib_dir=jq_lib_dir,
            commands=[
                ["./configure", "CFLAGS=-fPIC -pthread", "--disable-maintainer-mode", "--with-oniguruma=builtin"],
                ["make"],
            ])

    def _build_lib(self, tarball_path, lib_dir, commands):
        self._extract_tarball(
            tarball_path=tarball_path,
            lib_dir=lib_dir,
        )

        macosx_deployment_target = sysconfig.get_config_var("MACOSX_DEPLOYMENT_TARGET")
        if macosx_deployment_target:
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = str(macosx_deployment_target)

        def run_command(args):
            print("Executing: %s" % ' '.join(args))

            if os.name == "nt":
                command = ["msys2.cmd", "-c", " ".join(shlex.quote(arg) for arg in args)]
            else:
                command = args

            subprocess.check_call(command, cwd=lib_dir)

        for command in commands:
            run_command(command)

    def _extract_tarball(self, tarball_path, lib_dir):
        if os.path.exists(lib_dir):
            shutil.rmtree(lib_dir)
        tarfile.open(tarball_path, "r:gz").extractall(_dep_build_path("."))


use_system_libs = bool(os.environ.get("JQPY_USE_SYSTEM_LIBS"))


if use_system_libs:
    jq_build_ext = build_ext
    link_args_deps = ["-ljq", "-lonig"]
    extra_objects = []
else:
    jq_build_ext = jq_with_deps_build_ext
    link_args_deps = []
    extra_objects = [
        os.path.join(jq_lib_dir, ".libs/libjq.a"),
        os.path.join(jq_lib_dir, "vendor/oniguruma/src/.libs/libonig.a"),
    ]

jq_extension = Extension(
    "jq",
    sources=["jq.pyx"],
    # MS_WIN64 has to be set to successfully build when using MinGW for 64-bit
    # Windows. See: https://github.com/cython/cython/issues/2670
    define_macros=[("MS_WIN64" , 1)] if os.name == "nt" and sys.maxsize > 2**32  else None,
    include_dirs=[os.path.join(jq_lib_dir, "src")],
    extra_link_args=["-lm"] + (["-Wl,-Bstatic", "-lpthread", "-lshlwapi", "-static-libgcc"] if os.name == 'nt' else []) + link_args_deps,
    extra_objects=extra_objects,
)

setup(
    name='jq',
    version='1.10.0',
    description='jq is a lightweight and flexible JSON processor.',
    long_description=_read("README.rst"),
    author='Michael Williamson',
    url='https://github.com/mwilliamson/jq.py',
    python_requires='>=3.8',
    license='BSD 2-Clause',
    ext_modules = cythonize([jq_extension]),
    cmdclass={"build_ext": jq_build_ext},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)

