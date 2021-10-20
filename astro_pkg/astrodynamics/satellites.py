from __future__ import annotations
import datetime
import typing

import numpy as np
from orbit_predictor.predictors.accurate import HighAccuracyTLEPredictor
from orbit_predictor.coordinate_systems import ecef_to_llh


class LLH(typing.NamedTuple):
    datetime: typing.Sequence[datetime.datetime]
    latitude: np.typing.NDArray[float]
    longitude: np.typing.NDArray[float]
    altitude: np.typing.NDArray[float]


class SatellitePredictor(HighAccuracyTLEPredictor):
    """
    Predictor for satellite overpasses. Uses sgp4 for propagation
    """
    def __init__(self, satid: int):
        """
        Params:
            satid: int = NORAD id for satellite
            source: PasspredictTLESource
        """
        self.satid = satid
        self._source = None
        self.tle = None
        self._propagator = None

    @property
    def sate_id(self):
        return self.satid

    def set_propagator(self):
        self._propagator = self._get_propagator()

    def get_only_position(self, datetime: datetime.datetime) -> np.ndarray:
        """
        Get satellite position in ECEF coordinates [km]
        """
        pos_tuple = super().get_only_position(datetime)
        return np.array(pos_tuple)

    def get_llh(self, datetime: datetime.datetime) -> np.ndarray:
        """"""

    def get_position_detail(self, start_date, n_steps, time_step):
        """
        Get satellite subpoints and details
        """
        latitude = np.empty(n_steps)
        longitude = np.empty(n_steps)
        altitude = np.empty(n_steps)
        datetime = [None] * n_steps
        dt = start_date
        for i in range(n_steps):
            recef = self.get_only_position(dt)
            lat, lon, h = ecef_to_llh(recef)
            latitude[i] = lat
            longitude[i] = lon
            altitude[i] = h
            datetime[i] = dt
            dt += time_step
        return LLH(datetime, latitude, longitude, altitude)
