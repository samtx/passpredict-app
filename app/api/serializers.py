from typing import List

from orbit_predictor.predictors import PredictedPass

from .schemas import Location, Satellite, Overpass, SingleSatOverpassResult, Point




def single_overpass_result_serializer(data: List[PredictedPass]) -> str:
    """
    Serialize the list of PredictedPass objects to json string
    """
    print(data[0])
    overpasses = []
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
    overpasses = overpass_serializer(data)
    out = SingleSatOverpassResult(location=location, overpasses=overpasses, satellite=satellite)
    return out.json()


def overpass_serializer(pass_list: List[PredictedPass]) -> List[Overpass]:
    """
    Serialize individual overpass data
    """
    for pass_ in pass_list:
        aos_dt = pass_.aos


