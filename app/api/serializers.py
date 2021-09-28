from typing import List
from zoneinfo import ZoneInfo
from datetime import datetime, timezone as py_timezone

from orbit_predictor.predictors import PredictedPass
from timezonefinder import TimezoneFinder

from .schemas import Location, Satellite, Point, Overpass, SingleSatOverpassResult, Point


tf = TimezoneFinder()


def single_overpass_result_serializer(data: List[PredictedPass]) -> str:
    """
    Serialize the list of PredictedPass objects to json string
    """
    # print(data[0])
    op_location = data[0].location
    location_h = round(op_location.elevation_m, 0)
    location_lat = round(op_location.latitude_deg, 4)
    location_lon = round(op_location.longitude_deg, 4)
    location_name = op_location.name
    location = Location(
        lat=location_lat, lon=location_lon, h=location_h, name=location_name
    )
    satid = data[0].satid
    satellite = Satellite(id=satid)
    # Find timezone
    tz_str = tf.timezone_at(lng=location.lon, lat=location.lat)
    if tz_str is None:
        tz = py_timezone.utc
    else:
        tz = ZoneInfo(tz_str)
    overpasses = overpass_serializer(data, tz=tz)
    out = SingleSatOverpassResult(location=location, overpasses=overpasses, satellite=satellite)
    return out


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
        overpass = Overpass(
            aos=aos,
            tca=tca,
            los=los,
            duration=round(pass_.duration, 1),
            satid=pass_.satid,
            max_elevation=tca.el
        )
        overpasses.append(overpass)
    return overpasses


def passpoint_serializer(passpoint, tz: ZoneInfo):
    """ Serialize overpass point """
    dt_local = passpoint.dt.astimezone(tz)
    timestamp = dt_local.timestamp()
    az = round(passpoint.azimuth, 2)
    el = round(passpoint.elevation, 2)
    range_ = round(passpoint.range, 3)
    return Point(
        datetime=dt_local,
        timestamp=timestamp,
        az=az,
        el=el,
        range=range_
    )

