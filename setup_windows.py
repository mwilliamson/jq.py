#!/usr/bin/env python

import hashlib
import io
import os
import sys
import tarfile
import tempfile
from pathlib import Path

import requests
import zstandard as zstd
from Cython.Build import cythonize
from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension

PREFIX = tempfile.gettempdir()

windows_dependencies_manifest = {
    'oniguruma': [
        'https://repo.msys2.org/mingw/x86_64/mingw-w64-x86_64-oniguruma-6.9.5-1-any.pkg.tar.xz',
        "91ca8fb55267fbc11c45255df5e8b8a905b9d5b3695b768787988eaffafc582a",
    ],
    'gcc-libs': [
        'https://repo.msys2.org/mingw/x86_64/mingw-w64-x86_64-gcc-libs-10.2.0-1-any.pkg.tar.zst',
        "9267b2c4549c5000f13a9c92c58b134d1de2a652e55f78e6d89bb64a87dbc601",
    ],
    'gcc': [
        'https://repo.msys2.org/mingw/x86_64/mingw-w64-x86_64-gcc-10.2.0-1-any.pkg.tar.zst',
        '4fd970ece990306b5ea6fe768839dcd5a4bb103d1d3a30f399f9dbd3735fca19',
    ],
    'crt': [
        'https://repo.msys2.org/mingw/x86_64/mingw-w64-x86_64-crt-git-8.0.0.5966.f5da805f-1-any.pkg.tar.zst',
        '16ab39979007e03694acfbeaf204f9479ffc6c4e9bff0705a65040fa91f4903e',
    ],
    'jq': [
        'https://repo.msys2.org/mingw/x86_64/mingw-w64-x86_64-jq-1.6-3-any.pkg.tar.zst',
        "2144f7e0190f82d74311852d7701b3b6963f8d705706a08a0d999e1ce800477c",
    ],
    'libwinpthread': [
        'https://repo.msys2.org/mingw/x86_64/mingw-w64-x86_64-libwinpthread-git-8.0.0.5906.c9a21571-1-any.pkg.tar.zst',
        "f096bd6fbfd639bb70271313b4a45bc47a4de2ba7905d83a1345d8dc08885899",
    ],
}


def absolute(path: str) -> str:
    return str(Path(path).absolute())


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class BuildExt(build_ext):
    def run(self):
        self.prepare_windows_build_dependencies()
        super().run()

    def download(self, url: str, file_hash: str) -> bytes:
        # blob is small, no need to read by chunk
        resp = requests.get(url)
        if resp.status_code != 200:
            raise Exception("status code was: {}".format(resp.status_code))

        checksum = hashlib.sha256(resp.content).hexdigest()
        if file_hash != checksum:
            raise Exception('Hash mismatch. Expected {}, got {}'.format(file_hash, checksum))

        return resp.content


    def prepare_windows_build_dependencies(self):
        """Download, extract, and patch dependency files"""
        for _, (url, file_hash) in windows_dependencies_manifest.items():
            print('Fetching {}'.format(url))
            binary = self.download(url, file_hash)
            print('Got      {}'.format(url))

            with io.BytesIO(binary) as stream_fp:
                if url.endswith('.zst'):
                    xz_fp = io.BytesIO()
                    dctx = zstd.ZstdDecompressor()
                    with dctx.stream_reader(stream_fp) as reader:
                        while True:
                            chunk = reader.read()
                            xz_fp.write(chunk)
                            if not chunk:
                                break

                    xz_fp.seek(0)
                    tarfile.open(fileobj=xz_fp).extractall(path=PREFIX)
                    xz_fp.close()
                else:
                    tarfile.open(fileobj=stream_fp).extractall(path=PREFIX)

        # self.patch_jv_header(rf'{TMP}\mingw64\include\jv.h')
        self.patch_jv_header(rf'{PREFIX}/mingw64/include/jv.h')


    def patch_jv_header(self, path):
        with open(path, 'r+') as file:
            lines = file.readlines()
            lines.insert(103, '#define JV_PRINTF_LIKE(fmt_arg_num, args_num)\n')
            lines.insert(104, '#define JV_VPRINTF_LIKE(fmt_arg_num)\n')
            file.seek(0)
            file.writelines(lines)


def win_setup():
    extension = Extension(
        "jq",
        sources=["jq.pyx"],
        include_dirs=[absolute(f'{PREFIX}/mingw64/include')],
        library_dirs=[absolute(f'{PREFIX}/mingw64/lib')],
        extra_objects=list(map(absolute, [
            f'{PREFIX}/mingw64/lib/gcc/x86_64-w64-mingw32/10.2.0/libgcc_s.a',
            f'{PREFIX}/mingw64/lib/gcc/x86_64-w64-mingw32/10.2.0/libgcc_eh.a',
            f'{PREFIX}/mingw64/lib/gcc/x86_64-w64-mingw32/10.2.0/libgcc.a',
            f'{PREFIX}/mingw64/x86_64-w64-mingw32/lib/libmingwex.a',
            f'{PREFIX}/mingw64/x86_64-w64-mingw32/lib/libshlwapi.a',
            f'{PREFIX}/mingw64/x86_64-w64-mingw32/lib/libmsvcrt.a',
            f'{PREFIX}/mingw64/lib/libjq.a',
            f'{PREFIX}/mingw64/lib/libonig.a',
        ]))
    )

    setup(
        name='jq',
        version='1.0.2',
        description='jq is a lightweight and flexible JSON processor.',
        long_description=read("README.rst"),
        author='Michael Williamson',
        url='http://github.com/mwilliamson/jq.py',
        python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
        license='BSD 2-Clause',
        ext_modules = cythonize(
            [extension],
            compiler_directives={'language_level': sys.version_info[0]},
        ),
        cmdclass={"build_ext": BuildExt},
        include_package_data=True,
        # https://docs.python.org/3/distutils/setupscript.html#distutils-additional-files 
        # The documentation says:

        # You can specify the data_files options as a simple sequence of files
        # without specifying a target directory, but this is not recommended, and
        # the install command will print a warning in this case. To install data
        # files directly in the target directory, an empty string should be given
        # as the directory.

        # Bullshit! I cannot use an empty string because of:

        # warning: install_data: setup script did not provide a directory for '' -- installing right in 'build\bdist.win-amd64\egg'
        # error: can't copy '': doesn't exist or not a regular file
        data_files=[
            f'{PREFIX}/mingw64/bin/libgcc_s_seh-1.dll',
            f'{PREFIX}/mingw64/bin/libwinpthread-1.dll',
        ],
    )
