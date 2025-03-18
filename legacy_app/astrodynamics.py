from __future__ import annotations
import datetime
from typing import Tuple, TYPE_CHECKING

from passpredict import (
    predict_single_satellite_overpasses,
    predict_next_overpass,
    Location,
    get_satellite_llh,
    PredictedPass,
    AsyncPasspredictTLESource,
    SGP4Predictor,
    TLE,
    Observer,
)
from passpredict.constants import R_EARTH

if TYPE_CHECKING:
    from passpredict import LLH

def get_next_pass_detail(
    satellite: SGP4Predictor,
    location: Location,
    date_start: datetime.datetime,
    min_elevation: float = 10.0,
) -> Tuple[PredictedPass, LLH]:
    observer = Observer(location, satellite, aos_at_dg=min_elevation, tolerance_s=1.0)
    pass_detail, llh = observer.next_pass_detail(date_start)
    return pass_detail, llh