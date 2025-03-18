from datetime import date, datetime
from uuid import UUID
from typing import Literal, Annotated, Any
from collections.abc import Iterator

from sqlalchemy.orm import Query
from sqlalchemy.sql.selectable import Select
from sqlalchemy import or_, func
from fastapi import Query
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    computed_field,
)

from api.settings import config
from api import db


class SatelliteDimensions(BaseModel):
    mass: float | None = Field(default=None, description="Mass in kilograms")
    length: float | None = Field(default=None, description="Length in meters")
    diameter: float | None = Field(default=None, description="Diameter in meters")
    span: float | None = Field(default=None, description="Span in meters")


class Satellite(BaseModel):
    model_config = ConfigDict(title="Satellite")

    norad_id: int
    intl_designator: str
    name: str
    # description: str | None = None
    # tags: list[str] = Field(default_factory=list)
    decay_date: date | None = None
    launch_date: date | None = None
    # dimensions: SatelliteDimensions | None = None


class SatelliteOut(Satellite):
    model_config = ConfigDict(title="Satellite", from_attributes=True)

    id: int | None = None


class SatelliteQueryFilter:

    def __init__(
        self,
        norad_id: Annotated[list[int], Query(description="Search by norad_id")] = [],
        intl_designator: Annotated[list[str], Query(description="Search by international designator or COSPAR ID")] = [],
        name: Annotated[list[str], Query(description="Search by satellite name")] = [],
        search: Annotated[str | None, Query(description="Wildcard search by satellite name and international designator. Use '*' or '%' for wildcard")] = None,
        launch_date: Annotated[date | None, Query(description="Search for satellites launched on this date")] = None,
        launch_date__lte: Annotated[date | None, Query(description="Search for satellites launched on or after this date")] = None,
        launch_date__gte: Annotated[date | None, Query(description="Search for satellites launched on or before this date")] = None,
        decayed: Annotated[bool, Query(description="Search for satellites that have decayed")] = False,
        decay_date: Annotated[date | None, Query(description="Search for satellites decayed on this date")] = None,
        decay_date__lte: Annotated[date | None, Query(description="Search for satellites decayed on or before this date")] = None,
        decay_date__gte: Annotated[date | None, Query(description="Search for satellites decayed on or after this date")] = None,
        order_by: Annotated[
            list[str],
            Query(
                description="Order results. Prefix field with '-' for descending order. Order value is ignored if full text search query 'q' is provided.",
            ),
        ] = ["norad_id"],
        limit: Annotated[int, Query(gt=0, lte=config.paginate.max_limit)] = config.paginate.max_limit,
        offset: Annotated[int, Query(gte=0)] = 0
    ):
        self.norad_id = list(norad_id)
        self.intl_designator = self._split_strings_and_lowercase(intl_designator)
        self.name = self._split_strings_and_lowercase(name)
        self.search = self._convert_wildcard(search)
        self.launch_date = launch_date
        self.launch_date__lte = launch_date__lte
        self.launch_date__gte = launch_date__gte
        self.decay_date__isnull = not decayed
        self.decay_date = decay_date
        self.decay_date__lte = decay_date__lte
        self.decay_date__gte = decay_date__gte
        self.order_by = order_by
        self.limit = limit
        self.offset = offset

    def _split_strings_and_lowercase(self, values: list[str]) -> list[str]:
        def splitter(x: str) -> Iterator[str]:
            for item in x.split(","):
                yield item.strip().lower()
        list_values = []
        for value in values:
            list_values.extend(splitter(value))
        return list_values

    def _convert_wildcard(cls, value: str | None) -> str | None:
        if not value:
            return value
        value = value.replace("*", "%")
        if "%" not in value:
            value = f"%{value}%"
        return value

    @property
    def _filtering_field_items(self) -> Iterator[tuple[str, Any]]:
        for field in (
            "norad_id",
            "name",
            "intl_designator",
            "launch_date",
            "launch_date__lte",
            "launch_date__gte",
            "decay_date__isnull",
            "decay_date",
            "decay_date__lte",
            "decay_date__gte",
        ):
            yield (field, getattr(self, field))


    @property
    def filtering_fields(self) -> Iterator[tuple[str, Any]]:
        for field, value in self._filtering_field_items:
            if value is None:
                continue
            if isinstance(value, list) and not value:
                continue
            yield (field, value)

    def filter(self, query: Select) -> Select:
        model_search_fields = {"name", "intl_designator"}
        lowercase_fields = model_search_fields
        for field_name, value in self.filtering_fields:
            if "__" in field_name:
                field_name, operator = field_name.split("__")
                operator, value = _sa_operator_map[operator](value)
                model_field = getattr(db.Satellite, field_name)
                model_field_comparison_fn = getattr(model_field, operator)
                query = query.filter(model_field_comparison_fn(value))
            else:
                operator = "__eq__"
                model_field = getattr(db.Satellite, field_name)
                if field_name in lowercase_fields:
                    model_field = func.lower(model_field)
                if len(value) > 1:
                    query = query.filter(model_field.in_(value))
                else:
                    query = query.filter(model_field.__eq__(value[0]))
        if self.search:
            search_filters = (getattr(db.Satellite, field).ilike(self.search) for field in model_search_fields)
            query = query.filter(or_(*search_filters))
        return query

    def sort(self, query: Select) -> Select:
        if not self.order_by:
            return query
        for field in self.order_by:
            direction = "desc" if field.startswith("-") else "asc"
            field = field.lstrip("-+")
            model_field = getattr(db.Satellite, field)
            model_field_order_by_fn = getattr(model_field, direction)
            query = query.order_by(model_field_order_by_fn())
        return query

    def paginate(self, query: Select) -> Select:
        if self.limit:
            query = query.limit(self.limit)
        if self.offset:
            query = query.offset(self.offset)
        return query


_sa_operator_map = {
    "gte": lambda value: ("__gte__", value),
    "lte": lambda value: ("__lte__", value),
    "isnull": lambda value: ("is_", None) if value is True else ("is_not", None),
}


class SatelliteQueryResponse(BaseModel):
    satellites: list[SatelliteOut]
    limit: int
    offset: int

    @computed_field
    @property
    def page_size(self) -> int:
        return len(self.satellites)


class OrbitQueryRequest(BaseModel):
    orbit_ids: list[UUID] = Field(alias="orbit_id", default_factory=list)
    norad_ids: list[int] = Field(alias="norad_id", default_factory=list)
    epoch_after: datetime | None = Field(default=None)
    epoch_before: datetime | None = Field(default=None)
    # originators: list[Literal['spacetrack', 'celestrak']] = Field(alias="originator", default_factory=list)
    created_after: datetime | None = Field(default=None)
    created_before: datetime | None = Field(default=None)
    page_size: int | None = Field(default=None, gt=0)
    cursor: str | None = None


class SatelliteSummary(BaseModel):
    model_config = ConfigDict(
        title="Satellite",
        from_attributes=True,
        extra="ignore",
    )

    id: int
    norad_id: int
    name: str | None = None


class OrbitOut(BaseModel):
    model_config = ConfigDict(
        title="Orbit",
        from_attributes=True,
        extra="ignore",
    )

    id: UUID
    epoch: datetime
    satellite: SatelliteSummary
    tle: str | None = Field(None, description="Two line element set")
    creation_date: datetime | None = None
    originator: str | None = None
    ref_frame: str | None = None
    time_system: str | None = None
    mean_element_theory: str | None = None
    mean_motion: float | None = None
    eccentricity: float | None = None
    ra_of_asc_node: float | None = None
    arg_of_pericenter: float | None = None
    mean_anomaly: float | None = None
    ephemeris_type: Literal[0, "SGP", "SGP4", "SDP4", "SGP8", "SDP8"] | None = None
    element_set_no: int | None = None
    rev_at_epoch: int | None = None
    bstar: float | None = None
    mean_motion_dot: float | None = None
    mean_motion_ddot: float | None = None
    perigee: float = Field(description="Orbit perigee in kilometers")
    apogee: float = Field(description="Orbit apogee in kilometers")
    inclination: float = Field(description="Orbit inclination in degrees")


class OrbitQueryResponse(BaseModel):
    model_config = model_config = ConfigDict(from_attributes=True)
    orbits: list[OrbitOut]
    page_size: int
    next_cursor: str | None = None
