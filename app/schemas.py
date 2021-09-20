import datetime
from typing import List, Optional
from enum import Enum
from math import floor

from pydantic import BaseModel, Field

from app.astrodynamics import jday2datetime
from app.utils import epoch_from_tle, satid_from_tle



class Tle(BaseModel):
    tle1: str
    tle2: str
    epoch: datetime.datetime
    satid: int

    @classmethod
    def from_string(cls, tle1: str, tle2: str):
        epoch = epoch_from_tle(tle1)
        satid = satid_from_tle(tle1)
        return cls(
            tle1=tle1,
            tle2=tle2,
            epoch=epoch,
            satid=satid,
        )

    def __hash__(self):
        hash_str = str(self.satid) + self.tle1 + self.tle2
        return hash(hash_str)

    class Config:
        title = 'TLE'




