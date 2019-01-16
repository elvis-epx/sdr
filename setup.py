#!/usr/bin/env python3

from distutils.core import setup
from Cython.Build import cythonize

setup(name='FM demodulation', ext_modules=cythonize("fastmodul.pyx"))
