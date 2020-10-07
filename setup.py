from setuptools import setup
from Cython.Build import cythonize

sourcefiles = []

ext = []
# ext = cythonize(
#     Extension(
        # []
# ext.append(cythonize(['passpredict/timefn_ext.pyx']))

setup(
    name="passpredict",
    ext_modules = ext,
    zip_safe = False,
)