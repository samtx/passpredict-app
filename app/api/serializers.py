from typing import List
from zoneinfo import ZoneInfo
from datetime import datetime, timezone as py_timezone

from astrodynamics import PredictedPass
from timezonefinder import TimezoneFinder

from .schemas import (
    Location,
    OrdinalDirection,
    Point,
    Overpass,
    SingleSatOverpassResult,
    Point,
    PassDetailResult,
)


tf = TimezoneFinder()


def single_satellite_overpass_result_serializer(
    location,
    satellite,
    data: List[PredictedPass]
) -> SingleSatOverpassResult:
    """
    Serialize the list of PredictedPass objects to json string
    """
    location_h = round(location.elevation_m, 0)
    location_lat = round(location.latitude_deg, 4)
    location_lon = round(location.longitude_deg, 4)
    location_name = location.name
    location = Location(
        lat=location_lat, lon=location_lon, h=location_h, name=location_name
    )
    # Find timezone
    tz_str = tf.timezone_at(lng=location.lon, lat=location.lat)
    if tz_str is None:
        tz = py_timezone.utc
    else:
        tz = ZoneInfo(tz_str)
    overpasses = overpass_serializer(data, tz=tz)
    out = SingleSatOverpassResult(location=location, overpasses=overpasses, satellite=satellite)
    return out


def satellite_pass_detail_serializer(
    location,
    satellite,
    pass_: PredictedPass
) -> PassDetailResult:
    """
    Serialize the list of PredictedPass objects to json string
    """
    location_h = round(location.elevation_m, 0)
    location_lat = round(location.latitude_deg, 4)
    location_lon = round(location.longitude_deg, 4)
    location_name = location.name
    location = Location(
        lat=location_lat, lon=location_lon, h=location_h, name=location_name
    )
    # Find timezone
    tz_str = tf.timezone_at(lng=location.lon, lat=location.lat)
    if tz_str is None:
        tz = py_timezone.utc
    else:
        tz = ZoneInfo(tz_str)
    overpass = overpass_serializer([pass_], tz=tz)[0]
    resp = PassDetailResult(location=location, satellite=satellite, overpass=overpass)
    return resp


def overpass_serializer(
    pass_list: List[PredictedPass],
    tz: ZoneInfo,
) -> List[Overpass]:
    """ Serialize individual overpass data """
    overpasses = []
    for pass_ in pass_list:
        aos = passpoint_serializer(pass_.aos, tz)
        tca = passpoint_serializer(pass_.tca, tz)
        los = passpoint_serializer(pass_.los, tz)
        max_elevation = max((aos.el, tca.el, los.el))
        overpass = Overpass(
            aos=aos,
            tca=tca,
            los=los,
            duration=round(pass_.duration, 1),
            satid=pass_.satid,
            max_elevation=max_elevation
        )
        overpasses.append(overpass)
    return overpasses


def passpoint_serializer(passpoint, tz: ZoneInfo):
    """ Serialize overpass point """
    dt_local = passpoint.dt.astimezone(tz)
    timestamp = dt_local.timestamp()
    az = round(passpoint.azimuth, 2)
    az_ord = OrdinalDirection.from_az(az).name
    el = round(passpoint.elevation, 2)
    range_ = round(passpoint.range, 3)
    return Point(
        datetime=dt_local,
        timestamp=timestamp,
        az=az,
        az_ord=az_ord,
        el=el,
        range=range_
    )