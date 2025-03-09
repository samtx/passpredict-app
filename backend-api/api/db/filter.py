
from typing import Any, Annotated

from fastapi import Query
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    ValidationInfo,
    StringConstraints,
)


LowerStr = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True)]


class ModelFilter(Filter):

    @field_validator("*", mode="before", check_fields=False)
    def split_str(cls, value: Any) -> list[Any]:
        return value


# class SatelliteQueryFilter(ModelFilter):
#     norad_id: int | None = Field(default=None, description="Search by norad_id")
#     intl_designator: str | None = Field(default=None, description="Search by international designator or COSPAR ID")
#     intl_designator__ilike: str | None = Field(default=None, description="Search for satellties by international designator or COSPAR ID. Use '*' as a wildcard character.")
#     name: str | None = Field(default=None)
#     name__ilike: str | None = Field(default=None, description="Search for satellites by name. Use '*' as a wildcard character.")
#     launch_date: date | None = Field(default=None, description="Search for satellites launched on this date")
#     launch_date__lte: date | None = Field(default=None, description="Search for satellites launched on or after this date")
#     launch_date__gte: date | None = Field(default=None, description="Search for satellites launched on or before this date")
#     decay_date: date | None = Field(default=None, description="Search for satellites decayed on this date")
#     decay_date__lte: date | None = Field(default=None, description="Search for satellites decayed on or before this date")
#     decay_date__gte: date | None = Field(default=None, description="Search for satellites decayed on or after this date")
#     decay_date__isnull: bool | None = Field(default=None, description="Search for satellites that have not decayed")
#     order_by: list[str] = Field(
#         default=["norad_id"],
#         description=(
#             "Order results. Prefix field with '-' for descending order. "
#             "Order value is ignored if full text search query 'q' is provided."
#         ),
#     )

#     class Constants(Filter.Constants):
#         model = db.Satellite
#         ordering_field_name = "order_by"



#     @field_validator("intl_designator__ilike", "name__ilike", mode="after")
#     @classmethod
#     def convert_wildcard(cls, value: str) -> str:
#         value = value.replace("*", "%")
#         if "%" not in value:
#             value = f"%{value}%"
#         return value