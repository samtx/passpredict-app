from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy as np


common_kw = {
    'libraries': ['sofa_c'],#, 'math'],
    'library_dirs': ['/home/sam/.local/lib/', '/usr/local/lib/'],
    'extra_link_args': ['--verbose'],
    'include_dirs': ['app/', '/home/sam/.local/include/', '/usr/include/', '/usr/local/include/', np.get_include()],
    'extra_compile_args': ['-O2'],
    'language': 'c'
    # define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
}

ext = [
    Extension(
        'app.astrodynamics._rotations',
        ['app/astrodynamics/_rotations.pyx', 'app/astrodynamics/crotations.c'],
        **common_kw,
    ),
    Extension(
        'app.astrodynamics._solar',
        ['app/astrodynamics/_solar.pyx', 'app/astrodynamics/crotations.c', 'app/astrodynamics/csolar.c'],
        **common_kw,
    ),
    Extension(
        'app.astrodynamics._overpass',
        ['app/astrodynamics/_overpass.pyx', 'app/astrodynamics/coverpass.c'],
        **common_kw,
    )
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