from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy as np


common_kw = {
    'libraries': ['sofa_c'],#, 'math'],
    'library_dirs': ['/home/sam/lib/', '/usr/local/lib/'],
    'extra_link_args': ['--verbose'],
    'include_dirs': ['app/', '/home/sam/include/', '/usr/include/', '/usr/local/include/', np.get_include()],
    'extra_compile_args': ['-O2'],
    'language': 'c'
    # define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
}

ext = [
    Extension(
        'app._rotations', 
        ['app/_rotations.pyx', 'app/crotations.c'],
        **common_kw,
    ),
    Extension(
        'app._solar',
        ['app/_solar.pyx', 'app/crotations.c', 'app/csolar.c'],
        **common_kw,
    ),
    Extension(
        'app._overpass',
        ['app/_overpass.pyx', 'app/coverpass.c'],
        **common_kw,
    )
]

setup(
    name="app",
    ext_modules = cythonize(ext, language_level="3"),#, gdb_debug=True),#, annotate=True),
    zip_safe = False,
)