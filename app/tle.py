from datetime import datetime, timedelta, timezone
from functools import cached_property

import requests
import numpy as np
from pydantic import BaseModel, Field

from .utils import grouper, satid_from_tle, epoch_from_tle, parse_tle
from .schemas import Tle



# class TleDB(BaseModel):
#     id: int
#     tle1: str
#     tle2: str
#     epoch: datetime.datetime
#     satellite_id: int
#     created: datetime.datetime


def get_orbit_data_from_celestrak(satellite_id):
    """

    Params:
        satellite_id : int
            NORAD satellite ID


    See https://celestrak.com/NORAD/documentation/gp-data-formats.php

    Can use the new celestrak api for satellite ID
    https://celestrak.com/NORAD/elements/gp.php?CATNR=25544&FORMAT=json

    for tle api:
    https://celestrak.com/satcat/tle.php?CATNR=25544

    Supplemental TLEs available: (not fully working as json)
    https://celestrak.com/NORAD/elements/supplemental/gp-index.php?GROUP=iss&FORMAT=json

    https://celestrak.com/NORAD/elements/supplemental/starlink.txt
    https://celestrak.com/NORAD/elements/supplemental/iss.txt
    
    """
    query = {
        'CATNR': satellite_id,
        'FORMAT': 'json'
    }
    url = 'https://celestrak.com/NORAD/elements/gp.php'
    r = requests.get(url, data=query)
    return r.json()


def parse_tles_from_celestrak(satellite_id=None):
    """
    Download current TLEs from Celestrak and save them to a JSON file
    
    """
    if satellite_id is None:
        url = 'https://celestrak.com/NORAD/elements/stations.txt'
        params = {}
    else:
        url = 'https://celestrak.com/satcat/tle.php'
        params = {'CATNR': satellite_id}
    r = requests.get(url, params=params, stream=True)
    tle_data = {}
    for tle_strings in grouper(r.text.splitlines(), 3):
        tle_data.update(parse_tle(tle_strings))
    return tle_data


def get_TLE(satid: int, tle_data=None) -> Tle:
    tle_data = parse_tles_from_celestrak(satid)
    tle1 = tle_data[satid]['tle1']
    tle2 = tle_data[satid]['tle2']
    tle = Tle.from_string(tle1=tle1, tle2=tle2)
    return tle
    

def save_TLE_data(url=None):
    tle_data = parse_tles_from_celestrak(url)
    with open('tle_data.json', 'w') as file:
        json.dump(tle_data, file)
