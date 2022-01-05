# cython: boundscheck=False, wraparound=False
# cython: language_level=3
# distutils: language = c

from libc.math cimport sin, cos, sqrt, atan, atan2, asin, pi, pow

import numpy as np
cimport numpy as np

cdef extern from "sofa.h":
    cdef double iauGmst82(double dj1, double dj2)
    cdef double iauEqeq94(double date1, double date2)
    cdef double iauObl80(double date1, double date2)
    cdef void iauNut80(double date1, double date2, double *dpsi, double *deps)
    cdef void iauNumat(double epsa, double dpsi, double deps, double rmatn[3][3])
    cdef int iauJd2cal(double dj1, double dj2, int *iy, int *im, int *id, double *fd)
    cdef int iauDat(int iy, int im, int id, double fd, double *deltat)


def razel(
    double location_lat_rad,
    double location_lon_rad,
    double[:] location_ecef,
    double[:] satellite_ecef
):
    """
    Get range, azimuth, and elevation of satellite relative for observing location
    """
    cdef double rx, ry, rz
    cdef double sin_location_lat, cos_location_lat
    cdef double sin_location_lon, cos_location_lon
    cdef double top_s, top_e, top_z
    cdef double range_, el, az, el_deg, az_deg

    rx = satellite_ecef[0] - location_ecef[0]
    ry = satellite_ecef[1] - location_ecef[1]
    rz = satellite_ecef[2] - location_ecef[2]

    sin_location_lat = sin(location_lat_rad)
    cos_location_lat = cos(location_lat_rad)
    sin_location_lon = sin(location_lon_rad)
    cos_location_lon = cos(location_lon_rad)

    top_s = (sin_location_lat * cos_location_lon * rx) + (sin_location_lat * sin_location_lon * ry) - (cos_location_lat * rz)
    top_e = -sin_location_lon * rx + cos_location_lon * ry
    top_z = (cos_location_lat * cos_location_lon * rx) + (cos_location_lat * sin_location_lon * ry) + (sin_location_lat * rz)

    range_ = sqrt(top_s*top_s + top_e*top_e + top_z*top_z)
    el = asin(top_z / range_)
    az = atan2(-top_e, top_s) + pi

    # convert radians to degrees
    el_deg = el * 180.0 / pi
    az_deg = az * 180.0 / pi

    return (range_, az_deg, el_deg)


def ecef_to_llh(double[:] recef):
    """
    Convert ECEF coordinates to latitude, longitude, and altitude
    Uses WGS84 constants
    Based on orbit_predictor.coordinate_systems.ecef_to_llh
    """
     # WGS-84 ellipsoid parameters */
    cdef double a = 6378.1370
    cdef double b = 6356.752314
    cdef double p, thet, esq, epsq, lat, lon, h, n

    p = sqrt(recef[0]*recef[0] + recef[1]*recef[1])
    thet = atan(recef[2] * a / (p * b))
    esq = 1.0 - (b / a)*(b / a)
    epsq = (a / b)*(a / b) - 1.0

    lat = atan((recef[2] + epsq * b * pow(sin(thet), 3)) / (p - esq * a * pow(cos(thet), 3)))
    lon = atan2(recef[1], recef[0])
    n = a*a / sqrt(a*a*cos(lat)*cos(lat) + b*b*sin(lat)*sin(lat))
    h = p / cos(lat) - n

    lat = lat * 180.0 / pi  # convert from radians to degrees
    lon = lon * 180.0 / pi
    return lat, lon, h


cpdef double jd2tt(double jd):
    """
    Convert julian date to terrestial time. Don't apply corrections for UT1
    """
    cdef double day_fraction, delta_at, tai, tt
    cdef int err, year, month, day

    # Find terrestial time, ignore delta_UT1
    err = iauJd2cal(jd, 0.0, &year, &month, &day, &day_fraction)
    # Have some error checking here, if err != 0
    err = iauDat(year, month, day, day_fraction, &delta_at)
    tai = jd + delta_at/86400.0
    tt = tai + 32.184/86400.0
    #tt -= DJ00;   // Leave terrestial time in J2000 format
    return tt


def mod2ecef():
    pass