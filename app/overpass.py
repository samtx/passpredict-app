from datetime import datetime, timedelta, date, timezone
from typing import List, Callable
import time
import pickle

from astropy.time import Time
from numpy import ndarray
import numpy as np
from scipy.interpolate import interp1d

from .solar import compute_sun_data
from .propagate import compute_satellite_data
from .timefn import julian_date_array_from_date, jday2datetime
from .schemas import Overpass, Location, Satellite, OverpassResult, Point
from .models import Sun, RhoVector, Sat, SatPredictData, PassType
from .tle import get_TLE
from .constants import RAD2DEG, DAY_S
from .rotations import ecef2sez
from .topocentric import site_ECEF
from .settings import MAX_DAYS
from .cache import cache, set_sat_cache, set_sun_cache, get_sat_cache, get_sun_cache
from .utils import get_visible_satellites


VISIBLE_SATS = get_visible_satellites()
print(f'{len(VISIBLE_SATS)} visible satellites found')


DT_SECONDS = 120
# Make sure that dt_seconds evenly divides into number of seconds per day
assert DAY_S % DT_SECONDS == 0 
NUM_TIMESTEPS_PER_DAY = int(DAY_S / DT_SECONDS)
TIME_KEY_SUFFIX = ':' + str(MAX_DAYS) + ':' + str(DT_SECONDS)


class RhoVector:
    def __init__(self, jd, rSEZ):
        self.jd = jd
        self.rSEZ = rSEZ      
        self.rng = self._compute_range()
        self.el = self._compute_elevation()

    def _compute_range(self):
        return np.linalg.norm(self.rSEZ, axis=0)

    def _compute_elevation(self):
        return np.arcsin(self.rSEZ[2] / self.rng) * RAD2DEG

    def _azimuth_from_idx(self, idx):
        rS = self.rSEZ[0, idx]
        rE = self.rSEZ[1, idx]
        tmp = np.arctan2(rS, rE)
        az = (tmp + np.pi * 0.5) * RAD2DEG
        if rS < 0 and rE < 0:
            az %= 360 
        return az

    def point(self, idx):
        p = Point.construct(
            datetime=jday2datetime(self.jd[idx]),
            azimuth=round(self._azimuth_from_idx(idx), 2),
            elevation=round(self.el[idx], 2),
            range=round(self.rng[idx], 3)
        )
        return p
    

def find_overpasses(
    sats: List[Sat],
    **kw
) -> List[Overpass]:
    """
    Real-time computation for finding satellite overpasses of a topographic location.
    Can support multiple satellites over a single location
    """
    store_sat_id = True if len(sats) > 1 else False
    overpasses = []
    for sat in sats:
        sat_overpasses = compute_single_satellite_overpasses(sat, store_sat_id=store_sat_id, **kw)    
        overpasses += sat_overpasses
    return overpasses


def compute_single_satellite_overpasses(sat, *, jd=None, location=None, sun_rECEF=None, min_elevation=10.0, visible_only=False, store_sat_id=True, sunset_el=-8.0):
    r_site_ECEF = site_ECEF(location.lat, location.lon, location.height)[:, np.newaxis]
    rho_ECEF = sat.rECEF - r_site_ECEF
    rSEZ = ecef2sez(rho_ECEF, location.lat, location.lon)
    # use cubic splines to interpolate the 
    n = jd.size
    rSEZ_interp = np.empty((3, (n-1)*DT_SECONDS), dtype=np.float64) 
    jd_interp = np.linspace(jd[0], jd[n-1], (n-1)*DT_SECONDS, endpoint=True)
    fn = interp1d(jd, rSEZ, kind='cubic', fill_value='extrapolate', assume_sorted=True)
    rSEZ_interp = fn(jd_interp)
    rho = RhoVector(jd_interp, rSEZ_interp)
    start_idx, end_idx = _start_end_index(rho.el - min_elevation)
    num_overpasses = min(start_idx.size, end_idx.size)       # Iterate over start/end indecies and gather inbetween indecies
    if start_idx.size < end_idx.size:
        end_idx = end_idx[1:]
    overpasses = [None]*num_overpasses if not visible_only else []
    for j in range(num_overpasses):
        # Store indecies of overpasses in a list
        idx0 = start_idx[j]
        idxf = end_idx[j]
        idxmax = np.argmax(rho.el[idx0:idxf+1])
        start_pt = rho.point(idx0)
        max_pt = rho.point(idx0 + idxmax)
        end_pt = rho.point(idxf)
        # Find visible start and end times
        if sun_rECEF is not None:
            sun_rho_ECEF = sun_rECEF[:,idx0:idxf+1] - r_site_ECEF
            sun_sez = ecef2sez(sun_rho_ECEF, location.lat, location.lon)
            sun_rng = np.linalg.norm(sun_sez, axis=0)
            sun_el = np.arcsin(sun_sez[2] / sun_rng) * RAD2DEG
            site_in_sunset = sun_el - sunset_el < 0
            site_in_sunset_idx = np.nonzero(site_in_sunset)[0]
            if site_in_sunset_idx.size == 0:
                passtype = PassType.daylight # site is always sunlit, so overpass is in daylight
            else:
                # get satellite illumination values for this overpass
                sat_visible = (sat.illuminated[idx0:idxf+1] * site_in_sunset)
                if np.any(sat_visible):
                    passtype = PassType.visible # site in night, sat is illuminated
                    sat_visible_idx = np.nonzero(sat_visible)[0]
                    sat_visible_start_idx = sat_visible_idx.min()
                    sat_visible_end_idx = sat_visible_idx.max()
                    vis_start_pt = point(idx0 + sat_visible_start_idx)
                    vis_end_pt = rho.point(idx0 + sat_visible_end_idx)
                    brightness_idx = np.argmax(rho.el[idx0 + sat_visible_start_idx: idx0 + sat_visible_end_idx + 1])
                    sat_rho = rho_rECEF[:, idx0 + sat_visible_start_idx + brightness_idx]
                    sat_rng = rho.rng[idx0 + sat_visible_start_idx + brightness_idx]
                    sun_rho_b = sun_rho[:, sat_visible_start_idx + brightness_idx]
                    sun_rng_b = sun_rng[sat_visible_start_idx + brightness_idx]
                    sat_site_sun_angle = math.acos(  
                        np.dot(sat_rho, sun_rho_b) / (sat_rng * sun_rng_b)
                    )
                    beta = math.pi - sat_site_sun_angle  # phase angle: site -- sat -- sun angle
                    brightness = sat.intrinsic_mag - 15 + 5*math.log10(sat_rng) - 2.5*math.log10(math.sin(beta) + (math.pi - beta)*math.cos(beta))
                else:
                    passtype = PassType.unlit  # nighttime, not illuminated (radio night)
        else:
            passtype = None

        if visible_only and passtype != PassType.visible:
            continue

        overpass_dict = {
            'start_pt': start_pt,
            'max_pt': max_pt,
            'end_pt': end_pt,
        }
        if store_sat_id:
            overpass_dict['satellite_id'] = sat.id
        if (passtype is not None) and (passtype == PassType.visible):
            overpass_dict['vis_start_pt'] = vis_start_pt
            overpass_dict['vis_end_pt'] = vis_end_pt
            overpass_dict['brightness'] = round(brightness, 2)
        overpass_dict['type'] = passtype
        overpass = Overpass.construct(**overpass_dict)
        if not visible_only:
            overpasses[j] = overpass
        else:
            overpasses.append(overpass)
    return overpasses


def predict_single_satellite_overpasses(
    satid: int,
    lat: float,
    lon: float,
    date_start: datetime,
    *,
    days: int = 10,
    min_elevation: float = 10.0,
    visible_only: bool = False,
    h: float = 0.0   # Altitude [m]
) -> OverpassResult:
    """
    Full prediction algorithm:
      1. Download TLE data
      2. Propagate satellite using SGP4
      3. Predict overpasses based on site location
      4. Return overpass object and print to screen

    Params:
        location : Location object
            latitude of site location, in decimal, north is positive
        satellite: Satellite object
            satellite ID number in Celestrak, ISS is 25544
    """
    date_end = date_start + timedelta(days=days)  
    satellite = Satellite(id=satid)
    location = Location(lat=lat, lon=lon, h=h)
    jd = julian_date_array_from_date(date_start, date_end, DT_SECONDS)
    time_key = 'time:' + date_start.strftime('%Y%m%d') + TIME_KEY_SUFFIX
    sun_key = 'sun:' + time_key
    sat_key = 'sat:' + str(satid) + ':' + time_key
    with cache.pipeline() as pipe:
        pipe.hgetall(sun_key)
        pipe.hgetall(sat_key)
        sun, sat = pipe.execute()
        if not sun:
            t = Time(jd, format='jd')
            sun_rECEF = compute_sun_data(t)
            pipe = set_sun_cache(sun_key, sun_rECEF, pipe, 86400)
        else:
            sun_rECEF = get_sun_cache(sun)
        if not sat:
            tle = get_TLE(satellite.id)
            t = Time(jd, format='jd')
            sat = compute_satellite_data(tle, t, sun_rECEF)
            pipe = set_sat_cache(sat_key, sat, pipe, 86400)
        else:
            sat = get_sat_cache(sat, satid)
        pipe.execute()
    # sun_rECEF = sun.rECEF  # we only need the position data
    # Only use slice of position and time arrays requested
    if days < MAX_DAYS:
        end_index = NUM_TIMESTEPS_PER_DAY * days
        jd = jd[:end_index]
        sun_rECEF = sun_rECEF[:end_index]
        sat = SatPredictData(
            id=sat.id,
            rECEF=sat.rECEF[:, :end_index],
            illuminated=sat.illuminated[:end_index],
            sun_sat_dist=sat.sun_sat_dist[:end_index],
            intrinsinc_mag=sat.intrinsinc_mag
        )
    overpasses = compute_single_satellite_overpasses(
        sat,
        jd=jd, 
        location=location, 
        sun_rECEF=sun_rECEF, 
        min_elevation=min_elevation,
        visible_only=visible_only,
        store_sat_id=False
    )
    overpass_result = OverpassResult(
        location=location,
        satid=satid,
        overpasses=overpasses
    )
    return overpass_result


def predict_all_visible_satellite_overpasses(
    lat: float,
    lon: float,
    *,
    date_start: date = None,
    h: float = 0.0,
    min_elevation: float = 10.0,
):
    date_end = date_start + timedelta(days=1)
    location = Location(lat=lat, lon=lon, h=h)
    jd = julian_date_array_from_date(date_start, date_end, DT_SECONDS)
    time_key = 'time:' + date_start.strftime('%Y%m%d') + ':1:' + str(DT_SECONDS)
    sun_key = 'sun:' + time_key
    with cache.pipeline() as pipe:
        pipe.hgetall(sun_key)
        for satid in VISIBLE_SATS:
            sat_key = 'sat:' + str(satid) + ':' + time_key
            pipe.hgetall(sat_key)
        sun, *sats = pipe.execute()

        if not sun:
            t = Time(jd, format='jd')
            sun = compute_sun_data(t)
            pipe = set_sun_cache(sun_key, sun, pipe, 86400)
        else:
            sun = get_sun_cache(sun)
        
        num_visible_sats = len(VISIBLE_SATS)
        sat_list = [None] * num_visible_sats

        for i, satid, satdata in zip(range(num_visible_sats), VISIBLE_SATS, sats):
            if not satdata:
                print(f'Computing satellite position for satellite {satid}')
                tle = get_TLE(satid)
                t = Time(jd, format='jd')
                sat = compute_satellite_data(tle, t, sun)
                sat_key = 'sat:' + str(satid) + ':' + time_key
                pipe = set_sat_cache(sat_key, sat, pipe, 86400)
            else:
                sat = get_sat_cache(satdata, satid)
            sat_list[i] = sat

        overpasses = find_overpasses(jd, location, sat_list, sun, min_elevation, visible_only=True)
        overpass_result = OverpassResult(
            location=location,
            overpasses=overpasses
        )


def _start_end_index(x):
    """
    Finds the start and end indecies when a 1D array crosses zero
    """
    x0 = x[:-1]
    x1 = x[1:]
    x_change_sign = (x0*x1 < 0)   
    start_idx = np.nonzero(x_change_sign & (x0 < x1))[0]  # Find the start of an overpass
    end_idx = np.nonzero(x_change_sign & (x0 > x1))[0]    # Find the end of an overpass
    return start_idx, end_idx