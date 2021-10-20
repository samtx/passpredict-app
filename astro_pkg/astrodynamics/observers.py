from __future__ import annotations
import datetime
import typing
from math import radians, degrees, pi
from functools import cached_property
from dataclasses import dataclass

import numpy as np
from orbit_predictor.predictors.pass_iterators import LocationPredictor

from . import _rotations
from .exceptions import NotReachable, PropagationError
from .locations import Location
from .utils import get_pass_detail_datetime_metadata

if typing.TYPE_CHECKING:
    from .satellites import SatellitePredictor, LLH


class RangeAzEl(typing.NamedTuple):
    range: float  # km
    az: float     # deg
    el: float     # deg


@dataclass(frozen=True)
class PassPoint:
    dt: datetime                # datetime UTC
    range: float                # km
    azimuth: float              # deg
    elevation: float            # deg
    brightness: float = None    # magnitude brightness


class BasicPassInfo:
    """
    Holds basic pass information:
        aos datetime
        los datetime
        tca datetime
        max elevation
        duration (property)
        valid (property)
    """
    def __init__(
        self,
        aos_dt: datetime.datetime,
        tca_dt: datetime.datetime,
        los_dt: datetime.datetime,
        max_elevation: float
    ):
        self.aos_dt = aos_dt if aos_dt is not None else None
        self.tca_dt = tca_dt
        self.los_dt = los_dt if los_dt is not None else None
        self.max_elevation = max_elevation

    @property
    def aos(self):
        """ Backwards compatibilty from orbit_predictor """
        return self.aos_dt

    @property
    def tca(self):
        """ Backwards compatibilty from orbit_predictor """
        return self.tca_dt

    @property
    def los(self):
        """ Backwards compatibilty from orbit_predictor """
        return self.los_dt

    @property
    def valid(self):
        if (self.aos is None) or (self.los is None):
            return False
        return (self.max_elevation > 0)

    @cached_property
    def max_elevation_deg(self):
        return degrees(self.max_elevation)

    @cached_property
    def duration(self) -> datetime.timedelta:
        return self.los - self.aos


@dataclass
class PredictedPass:
    satid: int
    location: Location
    aos: PassPoint
    tca: PassPoint
    los: PassPoint
    azimuth: typing.Sequence[float] = None
    elevation: typing.Sequence[float] = None
    range: typing.Sequence[float] = None
    datetime: typing.Sequence[datetime.datetime] = None

    @cached_property
    def midpoint(self):
        """ Return datetime in UTC of midpoint of pass """
        midpt = self.aos.dt + (self.los.dt - self.aos.dt) / 2
        return midpt

    @cached_property
    def duration(self):
        """ Return pass duration in seconds """
        return (self.los.dt - self.aos.dt).total_seconds()

    def __repr__(self):
        return f"<PredictedPass {self.satid} over {repr(self.location)} on {self.aos.dt}"


class Observer(LocationPredictor):
    """
    Predicts passes of a satellite over a given location.
    Exposes an iterable interface.
    Notice that this algorithm is not fully exhaustive,
    see https://github.com/satellogic/orbit-predictor/issues/99 for details.
    """

    def __init__(
        self,
        location: Location,
        satellite: SatellitePredictor,
        max_elevation_gt=0,
        aos_at_dg=0,
        tolerance_s=1.0
    ):
        """
        Initialize Observer but also compute radians for geodetic coordinates
        """
        self.location = location
        self.satellite = satellite
        self.max_elevation_gt = radians(max([max_elevation_gt, aos_at_dg]))
        self.set_minimum_elevation(aos_at_dg)
        self.set_tolerance(tolerance_s)
        self.location_lat_rad = radians(self.location.latitude_deg)
        self.location_lon_rad = radians(self.location.longitude_deg)
        self.location_ecef = np.array(self.location.position_ecef)

    @property
    def predictor(self):
        """ For backwards compatibility """
        return self.satellite

    def iter_passes(self, start_date, limit_date=None):
        """Returns one pass each time"""
        current_date = start_date
        while True:
            if self._is_ascending(current_date):
                # we need a descending point
                ascending_date = current_date
                descending_date = self._find_nearest_descending(ascending_date)
                pass_ = self._refine_pass(ascending_date, descending_date)
                if pass_.valid:
                    if limit_date is not None and pass_.aos > limit_date:
                        break
                    predicted_pass = self._build_predicted_pass(pass_)
                    yield predicted_pass
                if limit_date is not None and current_date > limit_date:
                    break
                current_date = pass_.tca + self._orbit_step(0.6)
            else:
                current_date = self._find_nearest_ascending(current_date)

    @property
    def passes_over(self, *a, **kw):
        return self.iter_passes(*a, **kw)

    def get_next_pass(self,
        aos_dt: datetime.datetime,
        *,
        limit_date: datetime.datetime = None,
    ) -> PredictedPass:
        """
        Gets first overpass starting at aos_dt
        """
        pass_ = next(self.iter_passes(aos_dt, limit_date=limit_date))
        if not pass_:
            raise NotReachable('Propagation limit date exceeded')
        return pass_

    def get_next_pass_detail(
        self,
        aos_dt: datetime.datetime,
        *,
        limit_date: datetime.datetime = None,
        delta_s: float = 10,
        pad_minutes: int = 5,
    ) -> typing.Tuple[PredictedPass, LLH]:
        """
        Add details to PredictedPass
        Evaluate position and velocity properties for each delta_s seconds
        """
        pass_ = self.get_next_pass(aos_dt, limit_date=limit_date)
        start_date, n_steps, time_step = get_pass_detail_datetime_metadata(pass_, delta_s, pad_minutes=pad_minutes)
        pass_detail = self._get_overpass_detail(pass_, start_date, n_steps, time_step)
        llh = self.satellite.get_position_detail(start_date, n_steps, time_step)
        return (pass_detail, llh)

    def _get_overpass_detail(
        self,
        pass_,
        start_date: datetime.datetime,
        n_steps: int,
        time_step: datetime.timedelta,
    ):
        pass_.azimuth = np.empty(n_steps)
        pass_.elevation = np.empty(n_steps)
        pass_.range = np.empty(n_steps)
        pass_.datetime = [None] * n_steps
        dt = start_date
        for i in range(n_steps):
            rae = self.razel(dt)
            pass_.datetime[i] = dt
            pass_.azimuth[i] = rae.az
            pass_.elevation[i] = rae.el
            pass_.range[i] = rae.range
            dt += time_step
        return pass_

    def set_minimum_elevation(self, elevation: float):
        """  Set minimum elevation for an overpass  """
        self.aos_at = radians(elevation)
        self.aos_at_deg = elevation

    def set_tolerance(self, seconds: float):
        """  Set tolerance variables """
        if seconds <= 0:
            raise Exception("Tolerance must be > 0")
        self.tolerance_s = seconds
        self.tolerance = datetime.timedelta(seconds=seconds)

    def _build_predicted_pass(self, basic_pass: BasicPassInfo):
        """Returns a classic predicted pass"""
        aos = self.point(basic_pass.aos_dt)
        tca = self.point(basic_pass.tca_dt)
        los = self.point(basic_pass.los_dt)
        return PredictedPass(self.predictor.satid, self.location, aos, tca, los)

    def _find_nearest_descending(self, ascending_date):
        for candidate in self._sample_points(ascending_date):
            if not self._is_ascending(candidate):
                return candidate
        else:
            # logger.error('Could not find a descending pass over %s start date: %s - TLE: %s',
            #              self.location, ascending_date, self.predictor.tle)
            raise PropagationError("Can not find an descending phase")

    def _find_nearest_ascending(self, descending_date):
        for candidate in self._sample_points(descending_date):
            if self._is_ascending(candidate):
                return candidate
        else:
            # logger.error('Could not find an ascending pass over %s start date: %s - TLE: %s',
            #              self.location, descending_date, self.predictor.tle)
            raise PropagationError('Can not find an ascending phase')

    def _sample_points(self, date):
        """Helper method to found ascending or descending phases of elevation"""
        start = date
        end = date + self._orbit_step(0.99)
        mid = self.midpoint(start, end)
        mid_right = self.midpoint(mid, end)
        mid_left = self.midpoint(start, mid)
        return [end, mid, mid_right, mid_left]

    def _refine_pass(self, ascending_date, descending_date):
        tca_dt = self._find_tca(ascending_date, descending_date)
        elevation = self._elevation_at(tca_dt)
        if elevation > self.max_elevation_gt:
            aos_dt = self._find_aos(tca_dt)
            los_dt = self._find_los(tca_dt)
        else:
            aos_dt = los_dt = None
        return BasicPassInfo(aos_dt, tca_dt, los_dt, elevation)

    def _find_tca(self, ascending_date, descending_date):
        while not self._precision_reached(ascending_date, descending_date):
            midpoint = self.midpoint(ascending_date, descending_date)
            if self._is_ascending(midpoint):
                ascending_date = midpoint
            else:
                descending_date = midpoint
        return ascending_date

    def _precision_reached(self, start, end):
        return end - start <= self.tolerance

    @staticmethod
    def midpoint(start, end):
        """Returns the midpoint between two dates"""
        return start + (end - start) / 2

    def _elevation_at(self, when_utc):
        position = self.predictor.get_only_position(when_utc)
        return self.location.elevation_for(position)

    def _is_ascending(self, when_utc):
        """Check is elevation is ascending or descending on a given point"""
        elevation = self._elevation_at(when_utc)
        next_elevation = self._elevation_at(when_utc + self.tolerance)
        return elevation <= next_elevation

    def _orbit_step(self, size):
        """Returns a time step, that will make the satellite advance a given number of orbits"""
        step_in_radians = size * 2 * pi
        seconds = (step_in_radians / self.predictor.mean_motion) * 60
        return datetime.timedelta(seconds=seconds)

    def _find_aos(self, tca):
        end = tca
        start = tca - self._orbit_step(0.34)  # On third of the orbit
        elevation = self._elevation_at(start)
        assert elevation < 0
        while not self._precision_reached(start, end):
            midpoint = self.midpoint(start, end)
            elevation = self._elevation_at(midpoint)
            if elevation < self.aos_at:
                start = midpoint
            else:
                end = midpoint
        return end

    def _find_los(self, tca):
        start = tca
        end = tca + self._orbit_step(0.34)
        while not self._precision_reached(start, end):
            midpoint = self.midpoint(start, end)
            elevation = self._elevation_at(midpoint)
            if elevation < self.aos_at:
                end = midpoint
            else:
                start = midpoint
        return start

    def razel(self, datetime: datetime.datetime) -> RangeAzEl:
        """
        Get range, azimuth, and elevation for datetime
        """
        satellite_ecef = self.predictor.get_only_position(datetime)
        range_, az, el = _rotations.razel(
            self.location_lat_rad, self.location_lon_rad, self.location_ecef, satellite_ecef
        )
        return RangeAzEl(range_, az, el)

    def point(self, datetime: datetime.datetime) -> PassPoint:
        """
        Get PassPoint with range, azimuth, and elevation data for datetime
        """
        rnazel = self.razel(datetime)
        pt = PassPoint(datetime, rnazel.range, rnazel.az, rnazel.el)
        return pt