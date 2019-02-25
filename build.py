import os
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
from pprint import pprint

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

CUR_DIR = os.path.abspath(os.path.dirname(__file__))


class CMakeExt(Extension):
    def __init__(self, name, cmake_lists_dir='.', cmake_options=None, target='', **kwa):
        Extension.__init__(self, name, sources=[], **kwa)
        self.cmake_lists_dir = os.path.abspath(cmake_lists_dir)
        self.cmake_options = dict() if cmake_options is None else cmake_options
        self.target = target


class cmake_build_ext(build_ext):
    def build_extension(self, ext):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError('Cannot find CMake executable')
            pass

        extdir = os.path.abspath(os.path.dirname(
            self.get_ext_fullpath(ext.name)))
        build_dir = os.path.abspath(self.build_lib)
        pprint(build_dir)
        cfg = 'Debug' if 'CMAKE_BUILD_TYPE' not in ext.cmake_options else ext.cmake_options[
            'CMAKE_BUILD_TYPE']
        cmake_options = ext.cmake_options

        if platform.system() == 'Darwin' and shutil.which('brew', os.X_OK) and 'CMAKE_PREFIX_PATH' not in cmake_options:
            cmake_options['CMAKE_PREFIX_PATH'] = subprocess.check_output(
                ['brew', '--prefix', 'qt']).strip().decode('utf-8')

        ext_args = [
            '-D{}={}'.format(k, v) for k, v in ext.cmake_options.items() if k != 'CMAKE_BUILD_TYPE']

        cmake_args = [
            '-DCMAKE_BUILD_TYPE=%s' % cfg,
            '-DPYTHON_EXECUTABLE={}'.format(sys.executable),
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={}'.format(extdir),
            '-DCMAKE_ARCHIVE_OUTPUT_DIRECTORY={}'.format(self.build_temp),
        ] + ext_args

        # pprint(cmake_args)

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        # Config and build the extension
        subprocess.check_call(['cmake', ext.cmake_lists_dir] + cmake_args,
                              cwd=self.build_temp)
        cmake_build_args = ['cmake', '--build',
                            '.', '--config', cfg, '--', '-j2']
        if ext.target:
            cmake_build_args = ['cmake', '--build', '.',
                                '--config', cfg, '--target', ext.target, '--', '-j2']
        subprocess.check_call(cmake_build_args, cwd=self.build_temp)

    def get_ext_filename(self, ext_name):
        if platform.system() in ('cli', 'Windows'):
            suffix = '', '.dll'
        elif platform.system() in ('Darwin', ):
            suffix = '.dylib'
        else:
            suffix = '.so'
        return ext_name + suffix


EXTENSIONS = [
    CMakeExt(
        'vrep_gym/b0/libb0',
        'lib/bluezero',
        {'BUILD_GUI': 'ON'},
        'b0'
    ),
]


def build(setup_kwargs):
    """
    This function is mandatory in order to build the extensions.
    """
    setup_kwargs.update({
        'ext_modules': EXTENSIONS,
        'cmdclass': {
            'build_ext': cmake_build_ext,
        }
    })
