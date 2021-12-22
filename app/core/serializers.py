from __future__ import annotations
from typing import List, Union
from zoneinfo import ZoneInfo

from astrodynamics import PredictedPass

from .schemas import (
    Location,
    OrdinalDirection,
    OverpassDetail,
    Point,
    Overpass,
    Satellite,
    SingleSatOverpassResult,
    Point,
    PassDetailResult,
    SatelliteLatLng,
)


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
    tzinfo = location.timezone
    location = Location(
        lat=location_lat, lon=location_lon, h=location_h, name=location_name
    )
    overpasses = overpass_serializer(data, tz=tzinfo)
    satellite = Satellite(**satellite._asdict())  # convert to pydantic model
    res = SingleSatOverpassResult(location=location, overpasses=overpasses, satellite=satellite)
    return res


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
    tzinfo = location.timezone
    overpass = overpass_serializer([pass_], tz=tzinfo)[0]
    res = PassDetailResult(location=location, satellite=satellite, overpass=overpass)
    return res


def overpass_serializer(
    pass_list: List[PredictedPass],
    tz: ZoneInfo,
) -> Union[List[Overpass], List[OverpassDetail]]:
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
        if pass_.elevation is not None:
            # serialize OverpassDetail
            overpass = OverpassDetail(
                elevation=pass_.elevation.tolist(),
                azimuth=pass_.azimuth.tolist(),
                range=pass_.range.tolist(),
                datetime=pass_.datetime,
                **overpass.dict()
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


def satellite_latlng_serializer(
    satid,
    llh,
) -> SatelliteLatLng:
    """
    Serialize the satellite coordinates
    """
    latlng = [[round(lat, 6), round(lon, 6)] for (lat, lon) in zip(llh.latitude, llh.longitude)]
    timestamp = [d.timestamp() for d in llh.datetime]
    height = round(llh.altitude.mean(), 3)
    res = SatelliteLatLng(satid=satid, latlng=latlng, timestamp=timestamp, height=height)
    return res