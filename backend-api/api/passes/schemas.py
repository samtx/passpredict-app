from datetime import datetime
from typing import Annotated, Literal
from functools import partial
from math import ceil

from fastapi import Query
from pydantic import (
    BaseModel,
    Field,
    computed_field,
    AfterValidator,
    PlainSerializer,
)

from api.settings import config
from api.satellites.schemas import Satellite


Round6 = AfterValidator(partial(round, ndigits=6))
Round2 = AfterValidator(partial(round, ndigits=2))
FloatRound2 = Annotated[float, Round2]
Round1 = AfterValidator(partial(round, ndigits=1))

def format_milli(d: datetime) -> str:
    return d.isoformat(timespec="milliseconds").replace("+00:00", "Z")

FormatMilliseconds = PlainSerializer(format_milli, return_type=str, when_used="json-unless-none")


class Point(BaseModel):
    datetime: Annotated[datetime, FormatMilliseconds]
    azimuth: Annotated[float, Field(description='azimuth [deg]'), Round2]
    elevation: Annotated[float, Field(description='elevation [deg]'), Round2]
    range: Annotated[float, Field(description='range [km]'), Round2]
    # brightness: Annotated[float | None, Field(description='brightness magnitude')] = None


class Overpass(BaseModel):
    aos: Annotated[Point, Field(description='Acquisition of signal')]
    tca: Annotated[Point, Field(description='Time of closest approach')]
    los: Annotated[Point, Field(description='Loss of signal')]
    max_elevation: Annotated[float, Field(description='Maximum elevation [deg]'), Round2]
    norad_id: Annotated[int, Field(description='Satellite NORAD ID')]
    dt_razel: Annotated[list[tuple[datetime, FloatRound2, FloatRound2, FloatRound2]], Field(description="Array of (datetime, range [km], azimuth [km], elevation [deg]) for the overpass")] = []
    type: Literal["DAYLIGHT", "UNLIT", "VISIBLE"] | None = None
    # brightness: float = None
    vis_begin: Annotated[Point | None, Field(description='Satellite visibility begins')] = None
    vis_end: Annotated[Point | None, Field(description='Satellite visibility ends')] = None

    @computed_field(description='Duration of pass [sec]')
    @property
    def duration(self) -> int:
        delta = self.los.datetime.replace(microsecond=0) - self.aos.datetime.replace(microsecond=0)
        return int(ceil(delta.total_seconds()))


class Location(BaseModel):
    latitude: Annotated[float, Field(description='Location latitude, \u0b00N'), Round6]
    longitude: Annotated[float, Field(description='Location longitude, \u0b00E'), Round6]
    height: Annotated[float, Field(0.0, description='Location height above WGS84 ellipsoid [m]'), Round2]


class OverpassResult(BaseModel):
    location: Location
    satellites: list[Satellite]
    overpasses: list[Overpass]
    start: Annotated[datetime, FormatMilliseconds]
    end: Annotated[datetime, FormatMilliseconds]

    @computed_field
    @property
    def page_size(self) -> int:
        return len(self.overpasses)


class OverpassQuery:

    def __init__(
        self,
        norad_ids: Annotated[
            set[int],
            Query(min_length=1, max_length=config.predict.max_satellites, alias="norad_id", description="NORAD IDs of satellites to predict passes"),
        ],
        latitude: Annotated[
            float,
            Query(ge=-90, le=90, description="Location latitude in decimal degrees"),
        ],
        longitude: Annotated[
            float,
            Query(ge=-180, le=180, description="Location longitude in decimal degrees"),
        ],
        height: Annotated[
            float,
            Query(description="Location height in meters above WGS-84 ellipsoid"),
        ] = 0,
        days: Annotated[
            float,
            Query(gt=0, le=config.predict.max_days, description="Number of days to predict overpasses"),
        ] = config.predict.max_days,
    ):
        self.norad_ids = norad_ids
        self.latitude = round(float(latitude), 6)
        self.longitude = round(float(longitude), 6)
        self.height = round(float(height), 6)
        self.days = days
