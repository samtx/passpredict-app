# distutils: language = c

from libc.math cimport sin, cos, pi, asin, sqrt
import numpy as np
cimport numpy as np
cimport cython

from .constants import R_EARTH


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef sun_pos(double jd):
    """Compute the Sun position vector
    References:
        Vallado, p. 279, Alg. 29
        Vallado software, AST2BODY.FOR, subroutine SUN
    """
    cdef double t_ut1, lmda_Msun, t_tdb, M_sun, lmda_eclp, r_sun_mag, eps
    cdef double DEG2RAD = pi / 180.0   # degrees to radians
    cdef double AU_KM = 149597870.700  # AU to km
    r = np.empty(3, dtype=np.double)
    cdef double[::1] r_view = r

    t_ut1 = (jd - 2451545.0) / 36525
    t_tdb = t_ut1
    lmda_Msun = (280.4606184 + 36000.77005361 * t_tdb) % 360
    # M_sun = (357.5291092 + 35999.05034*t_tdb) % 360
    M_sun = (357.5277233 + 35999.05034 * t_tdb) % 360
    lmda_eclp = lmda_Msun + 1.914666471 * sin(M_sun * DEG2RAD)
    lmda_eclp += 0.019994643 * sin(2 * M_sun * DEG2RAD)
    r_sun_mag = 1.000140612 - 0.016708617 * cos(M_sun * DEG2RAD)
    r_sun_mag -= 0.000139589 * cos(2 * M_sun * DEG2RAD)
    eps = 23.439291 - 0.0130042 * t_tdb
    sinlmda = sin(lmda_eclp * DEG2RAD)
    r_view[0] = r_sun_mag * cos(lmda_eclp * DEG2RAD) * AU_KM
    r_view[1] = r_sun_mag * cos(eps * DEG2RAD) * sinlmda * AU_KM
    r_view[2] = r_sun_mag * sin(eps * DEG2RAD) * sinlmda * AU_KM
    return r


cpdef double sun_sat_angle(double[:] rsat, double[:] rsun):
    """Compute the sun-satellite angle
    Args:
        rsat : satellite position vector in ECI coordinates
        rsun : sun position vector in ECI coordinates
    Output:
        angle in radians between the two vectors
    References:
        Vallado, p. 912, Alg. 74
    """
    cdef double[:] cprod
    cdef double numer, denom, sinzeta, zeta

    # cross product
    # cprod[0] = a[1]*b[2] - a[2]*b[1]
    # cprod[1] = a[2]*b[0] - a[0]*b[2]
    # cprod[2] = a[0]*b[1] - a[1]*b[0]
    cprod = np.cross(rsun, rsat)
    numer = norm(cprod)
    denom = norm(rsun) * norm(rsat)
    sinzeta = numer / denom
    if (sinzeta > 1) and (1.0000003 > sinzeta):
        sinzeta = 1
    zeta = asin(sinzeta)
    return zeta


cpdef double sun_sat_orthogonal_distance(double[:] rsat, double zeta):
    """
    Args:
        rsat : satellite position vector in ECI coordinates
        zeta : angle in radians between the satellite and sun vectors
    Output:
        distance from satellite to center of Earth orthogonal to sun vector
    """
    return norm(rsat) * cos(zeta - pi*0.5)


def is_sat_illuminated(rsat, rsun):
    cdef double zeta, dist
    zeta = sun_sat_angle(rsat, rsun)
    dist = sun_sat_orthogonal_distance(rsat, zeta)
    return dist > R_EARTH


cdef double* cross(double[:] a, double[:] b):
    """
    Cross product between two vectors
    """
    cdef double[3] axb
    axb[0] = a[1]*b[2] - a[2]*b[1]
    axb[1] = a[2]*b[0] - a[0]*b[2]
    axb[2] = a[0]*b[1] - a[1]*b[0]
    return axb


cdef double norm(double[:] a):
    """
    L2 norm of vector
    """
    cdef double n
    n = sqrt(a[0]*a[0] + a[1]*a[1] + a[2]*a[2])
    return n
