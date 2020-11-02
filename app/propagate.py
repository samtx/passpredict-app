import numpy as np
from astropy import units as u
from astropy.coordinates import TEME, CartesianRepresentation, ITRS
from astropy.time import Time
from sgp4.api import Satrec, WGS84

from .solar import is_sat_illuminated, sat_illumination_distance
from .schemas import Tle
from .models import Sat, SatPredictData, SunPredictData

# import debugpy
# debugpy.debug_this_thread()

def propagate_satellite(tle1, tle2, jd, *args, **kwargs):
    """Propagate satellite position forward in time.

    Parameters:
        tle1 : str
            first line of two line element set
        tle2 : str
            second line of two line element set
        jd : float (n)
            array of julian dates to propagate

    Returns:
        r : float (3, n)
            satellite position vector in TEME coordinates
        v : float (3, n)
            satellite velocity vector in TEME coordinates
    """
    satrec = Satrec.twoline2rv(tle1, tle2, WGS84)
    jd_array, fr_array = np.divmod(jd, 1)
    error, r, v = satrec.sgp4_array(jd_array, fr_array)
    # Change arrays from column major to row major while keeping C-continuous
    r = np.reshape(r.ravel(order='F'), (3, r.shape[0]))
    v = np.reshape(v.ravel(order='F'), (3, v.shape[0]))
    return r, v


def compute_satellite_data(tle: Tle, t: Time, sun_rECEF: np.ndarray = None) -> SatPredictData:
    """
    Compute satellite data for Time
    
    Reference: 
        https://docs.astropy.org/en/latest/coordinates/satellites.html

    """
    r, _ = propagate_satellite(tle.tle1, tle.tle2, t.jd)
    # Use the TEME reference frame from astropy
    teme = TEME(CartesianRepresentation(r * u.km), obstime=t)
    ecef = teme.transform_to(ITRS(obstime=t))
    rECEF = ecef.data.xyz.value.astype(np.float32)  # extract numpy array from astropy object
    # sat.subpoint = ecef.earth_location
    # sat.latitude = sat.subpoint.lat.value
    # sat.longitude = sat.subpoint.lon.value
    
    if sun_rECEF is not None:
        sun_sat_dist = sat_illumination_distance(rECEF, sun_rECEF)
        illuminated = is_sat_illuminated(rECEF, sun_rECEF)
        satpredictdata = SatPredictData(id=tle.satid, rECEF=rECEF, illuminated=illuminated, sun_sat_dist=sun_sat_dist)
    else:
        satpredictdata = SatPredictData(id=tle.satid, rECEF=rECEF)
    return satpredictdata