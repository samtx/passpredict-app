from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy as np

ext = [
    Extension(
        'app._rotations', 
        ['app/_rotations.pyx', 'app/crotations.c'],
        libraries=['sofa_c'],#, 'math'],
        library_dirs=['/home/sam/lib/'],
        # extra_link_args=['--verbose'],
        include_dirs=['app/', '/home/sam/include/', '/usr/include/', '/usr/local/include/', np.get_include()],
        extra_compile_args=['-O3'],
        language='c'
    )
]

setup(
    name="app",
    ext_modules = cythonize(ext),
    zip_safe = False,
)