from setuptools import setup
from Cython.Build import cythonize

sourcefiles = []

ext = []
# ext = cythonize(
#     Extension(
        # []
# ext.append(cythonize(['passpredict/timefn_ext.pyx']))

setup(
    name="app",
    ext_modules = ext,
    zip_safe = False,
)