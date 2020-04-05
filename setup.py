import os
import subprocess
import tarfile
import shutil
from setuptools import setup

try:
    import sysconfig
except ImportError:
    # Python 2.6
    from distutils import sysconfig

try:
    import Cython
    from Cython.Build import cythonize
    _CYTHON_INSTALLED = True
except:
    _CYTHON_INSTALLED = False
    cythonize = lambda x: x

# The import of Extension must be after the import of Cython, otherwise
# we do not get the appropriately patched class.
# See https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html # noqa
from distutils.extension import Extension  # noqa: E402 isort:skip
from distutils.command.build import build  # noqa: E402 isort:skip

if _CYTHON_INSTALLED is True:
    from Cython.Distutils.old_build_ext import old_build_ext as _build_ext
else:
    from distutils.command.build_ext import build_ext as _build_ext

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

class jq_build_ext(_build_ext):
    def run(self):
        if _CYTHON_INSTALLED is False:
            raise UnimplementedError('This package requires Cython to build!')
        self._build_oniguruma()
        self._build_libjq()
        _build_ext.run(self)

    def _build_oniguruma(self):
        self._build_lib(
            source_url="https://github.com/kkos/oniguruma/releases/download/v5.9.6/onig-5.9.6.tar.gz",
            tarball_path=oniguruma_lib_tarball_path,
            lib_dir=oniguruma_lib_build_dir,
            commands=[
                ["autoreconf", "-i", "-f", "-W", "none"],
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

        def run_command(args, allow_failure=True):
            print("Executing: %s" % ' '.join(args))
            try:
                subprocess.check_call(args, cwd=lib_dir)
            except Exception as err:
                print(repr(err))
                print('Continuing ...')
            
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
        os.path.join(oniguruma_lib_install_dir, "lib/libonig.a")]
)

jq_cython_extension = Extension(
    "jq",
    sources=["jq.pyx"],
    include_dirs=[jq_lib_dir],
    extra_objects=[
        os.path.join(jq_lib_dir, ".libs/libjq.a"),
        os.path.join(oniguruma_lib_install_dir, "lib/libonig.a")]
)

setup(
    name='jq',
    version='0.1.6',
    description='jq is a lightweight and flexible JSON processor.',
    long_description=read("README.rst"),
    author='Michael Williamson',
    url='http://github.com/mwilliamson/jq.py',
    license='BSD 2-Clause',
    ext_modules=[jq_extension, jq_cython_extension],
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
        'Programming Language :: Python :: 3.5',
    ],
)

