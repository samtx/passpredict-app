# models.py
from dataclasses import dataclass, field

import numpy as np


@dataclass
class SatPredictData:
    # __slots__ = ['id', 'rECEF', 'illuminated', 'sun_sat_dist']
    id: int
    rECEF: np.ndarray         # dtype np.float64
    sun_sat_dist: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=np.float64))  # dtype np.float64
    intrinsic_mag: float = -1.8  # default for ISS

    def __getitem__(self, slc):
        return SatPredictData(
            id=self.id,
            rECEF=self.rECEF[:, slc],
            sun_sat_dist=self.sun_sat_dist[slc],
            intrinsic_mag=self.intrinsic_mag
        )
