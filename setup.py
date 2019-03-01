#!/usr/bin/env python3

from distutils.core import setup
from Cython.Build import cythonize

setup(name='FM stereo decoder with PLL', ext_modules=cythonize("fastfm.pyx"))
