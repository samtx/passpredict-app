import glob
from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy as np


common_kw = {
    'extra_link_args': ['--verbose'],
    'include_dirs': [
        'astrodynamics',
        'astrodynamics/sofa',
        'astrodynamics/sgp4',
        'astrodynamics/ast2body',
        np.get_include()
    ],
    'extra_compile_args': ['-O3'],
    'language': 'c++'
    # define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
}
source_files = []
source_files += glob.glob('astrodynamics/sofa/*.c')
source_files += glob.glob('astrodynamics/sgp4/*.cpp')
source_files += glob.glob('astrodynamics/ast2body/*.cpp')

ext = [
    Extension(
        'astrodynamics._time',
        ['astrodynamics/_time.pyx'] + source_files,
        **common_kw
    ),
    Extension(
        'astrodynamics._rotations',
        ['astrodynamics/_rotations.pyx'],
        **common_kw
    ),
]

setup(
    name="astrodynamics",
    packages=['astrodynamics'],
    ext_modules = cythonize(ext, language_level="3"),#, gdb_debug=True),#, annotate=True),
    zip_safe = False,
)