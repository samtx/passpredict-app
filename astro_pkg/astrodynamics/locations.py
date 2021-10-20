from functools import cached_property
from zoneinfo import ZoneInfo

from orbit_predictor.locations import Location as LocationBase

from .utils import get_timezone_from_latlon


class Location(LocationBase):

    @cached_property
    def timezone(self) -> ZoneInfo:
        """ Find timezone """
        return get_timezone_from_latlon(self.latitude_deg, self.longitude_deg)

    def __repr__(self):
        deg = u'\N{DEGREE SIGN}'
        s = '<Location '
        if self.name:
            s += self.name + ' '
        s += f'({self.latitude_deg}{deg} , {self.longitude_deg}{deg})'
        s += '>'
        return s
