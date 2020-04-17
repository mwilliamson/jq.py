#!/usr/bin/env python

import os
import platform
import subprocess
import tarfile
import shutil

import sysconfig

from setuptools import setup
from distutils.extension import Extension
from distutils.command.build_ext import build_ext

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

def path_in_dir(relative_path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


jq_lib_tarball_path = path_in_dir("_jq-lib-1.5.tar.gz")
jq_lib_dir = path_in_dir("jq-jq-1.5")

oniguruma_lib_tarball_path = path_in_dir("_onig-5.9.6.tar.gz")
oniguruma_lib_build_dir = path_in_dir("onig-5.9.6")
oniguruma_lib_install_dir = path_in_dir("onig-install-5.9.6")

class jq_build_ext(build_ext):
    def run(self):
        self._build_oniguruma()
        self._build_libjq()
        build_ext.run(self)

    def _build_oniguruma(self):
        self._build_lib(
            source_url="https://github.com/kkos/oniguruma/releases/download/v5.9.6/onig-5.9.6.tar.gz",
            tarball_path=oniguruma_lib_tarball_path,
            lib_dir=oniguruma_lib_build_dir,
            commands=[
                ["./configure", "CFLAGS=-fPIC", "--prefix=" + oniguruma_lib_install_dir],
                ["make"],
                ["make", "install"],
            ])


    def _build_libjq(self):
        self._build_lib(
            source_url="https://github.com/stedolan/jq/archive/jq-1.5.tar.gz",
            tarball_path=jq_lib_tarball_path,
            lib_dir=jq_lib_dir,
            commands=[
                ["autoreconf", "-i"],
                ["./configure", "CFLAGS=-fPIC", "--disable-maintainer-mode", "--with-oniguruma=" + oniguruma_lib_install_dir],
                ["make"],
            ])

    def _build_lib(self, source_url, tarball_path, lib_dir, commands):
        self._download_tarball(source_url, tarball_path)

        macosx_deployment_target = sysconfig.get_config_var("MACOSX_DEPLOYMENT_TARGET")
        if macosx_deployment_target:
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = macosx_deployment_target

        def run_command(args):
            print("Executing: %s" % ' '.join(args))
            subprocess.check_call(args, cwd=lib_dir)

        for command in commands:
            run_command(command)

    def _download_tarball(self, source_url, tarball_path):
        if os.path.exists(tarball_path):
            os.unlink(tarball_path)
        urlretrieve(source_url, tarball_path)

        if os.path.exists(jq_lib_dir):
            shutil.rmtree(jq_lib_dir)
        tarfile.open(tarball_path, "r:gz").extractall(path_in_dir("."))


jq_extension = Extension(
    "jq",
    sources=["jq.c"],
    include_dirs=[jq_lib_dir],
    extra_objects=[
        os.path.join(jq_lib_dir, ".libs/libjq.a"),
        os.path.join(oniguruma_lib_install_dir, "lib/libonig.a"),
    ],
)

setup(
    name='jq',
    version='0.1.7',
    description='jq is a lightweight and flexible JSON processor.',
    long_description=read("README.rst"),
    author='Michael Williamson',
    url='http://github.com/mwilliamson/jq.py',
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    license='BSD 2-Clause',
    ext_modules = [jq_extension],
    cmdclass={"build_ext": jq_build_ext},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)

