from typing import List
from zoneinfo import ZoneInfo
from datetime import timezone as py_timezone

from orbit_predictor.predictors import PredictedPass
from timezonefinder import TimezoneFinder

from .schemas import Location, Satellite, Overpass, SingleSatOverpassResult, Point


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
    satid = data[0].sate_id
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
    """
    Serialize individual overpass data
    """
    overpasses = []
    for pass_ in pass_list:
        context = {
            'aos_dt': pass_.aos.astimezone(tz),
            'max_dt': pass_.max_elevation_date.astimezone(tz),
            'los_dt': pass_.los.astimezone(tz),
            'duration': round(pass_.duration_s, 0),
            'max_elevation': round(pass_.max_elevation_deg, 2),
            'satellite_id': pass_.sate_id
        }
        overpass = Overpass(**context)
        overpasses.append(overpass)
    return overpasses

