import glob
from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy as np


common_kw = {
    'extra_link_args': ['--verbose'],
    'include_dirs': [
        'app/astrodynamics',
        'app/astrodynamics/sofa',
        'app/astrodynamics/sgp4',
        'app/astrodynamics/ast2body',
        np.get_include()
    ],
    'extra_compile_args': ['-O3'],
    'language': 'c++'
    # define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
}
source_files = []
source_files += glob.glob('app/astrodynamics/sofa/*.c')
source_files += glob.glob('app/astrodynamics/sgp4/*.cpp')
source_files += glob.glob('app/astrodynamics/ast2body/*.cpp')

ext = [
    Extension(
        'app.astrodynamics._time',
        ['app/astrodynamics/_time.pyx'] + source_files,
        **common_kw
    ),
    Extension(
        'app.astrodynamics._rotations',
        ['app/astrodynamics/_rotations.pyx'],
        **common_kw
    ),
]

setup(
    name="app",
    ext_modules = cythonize(ext, language_level="3"),#, gdb_debug=True),#, annotate=True),
    zip_safe = False,
    packages=['app'],
    install_requires=[
        'starlette',
        'uvicorn',
        'uvloop',
    ],
)