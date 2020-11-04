cimport cython

cimport numpy as np
import numpy as np

ctypedef np.float64_t DTYPE_f64_t

cdef extern from "crotations.h":
    void sun_mod2itrf(double *jd, double *r, int n);



def sun_pos(double[::1] jd):
    pass

@cython.boundscheck(False)
@cython.wraparound(False)
def sun_mod2ecef(np.ndarray[DTYPE_f64_t, ndim=1] jd, np.ndarray[DTYPE_f64_t, ndim=2] r):
    """
    Rotate position vector r from MOD -> J2000
    Using 1980 Nutation theory with GMST

    Inputs:
        jd, double[n]: Julian date floats
        r,  double[n, 3]: position vectors

    Outputs:
        r, double[n, 3]: rotated position vector rotated in-place

    Reference:
        Uses IAU SOFA iauNut80 and iauGMST82 function to compute rotation matrix
    """
    cdef int n
    n = jd.shape[0]
    
    cdef double[::1] jd_view = jd
    cdef double[::1] r_view = r.ravel()
    
    sun_mod2itrf(&jd_view[0], &r_view[0], n)
    r_view_array = np.asarray(r_view)
    r = r_view_array.reshape((n, 3))
    return r

      


