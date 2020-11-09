from datetime import datetime, timedelta, timezone
from functools import cached_property
import json
from typing import Dict, Set

import requests
import numpy as np
from pydantic import BaseModel, Field
from sqlalchemy.sql import select
from sqlalchemy import and_

from .utils import grouper, satid_from_tle, epoch_from_tle, parse_tle
from .schemas import Tle
from .database import engine
from .dbmodels import tle as tledb



# class TleDB(BaseModel):
#     id: int
#     tle1: str
#     tle2: str
#     epoch: datetime.datetime
#     satellite_id: int
#     created: datetime.datetime

def download_common_tles_from_celestrak() -> Set:
    """
    Download common tle data from celestrak
    """
    urls = [
        'https://www.celestrak.com/NORAD/elements/active.txt',
        'https://celestrak.com/NORAD/elements/visual.txt',
        'https://celestrak.com/NORAD/elements/stations.txt',
    ]
    tles = set()
    for url in urls:
        r = requests.get(url)
        print(f'request url {url}')
        for tle_strings in grouper(r.text.splitlines(), 3):
            tle = Tle.from_string(tle_strings[1], tle_strings[2])
            tles.add(tle)
    return tles


def import_tle_data_to_database(tle_data: Set) -> None:
    """
    Use SQLAlchemy to update database with tle data
    """
    # tle_data_list = [tle.dict() for tle in tle_data]
    created_at = datetime.utcnow()
    with engine.connect() as conn:
        for tle in tle_data:
            # Check if there is a tle for the datetime, 
            # if not then insert record, otherwise skip
            stmt = select([tledb]).where(
                and_(
                    tledb.c.satellite_id==tle.satid,
                    tledb.c.epoch==tle.epoch
                )
            )
            res = conn.execute(stmt).fetchone()
            if not res:
                stmt = tledb.insert({
                    'satellite_id': tle.satid,
                    'tle1': tle.tle1,
                    'tle2': tle.tle2,
                    'epoch': tle.epoch,
                    'created': created_at
                })
                res = conn.execute(stmt)
                print(f'Inserted sat {tle.satid} for epoch {tle.epoch} in db.')
            else:
                print(f'sat {tle.satid} for epoch {tle.epoch} already exists in db. skipping...')



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
    

def get_most_recent_tle(satid: int) -> Tle:
    """
    Queries database for most recent tle for satellite
    """
    with engine.connect() as conn:
        stmt = select([tledb]).where(
            tledb.c.satellite_id == satid
        ).order_by(
            tledb.c.epoch.desc()
        )
        res = conn.execute(stmt).fetchone()
        if res:
            tle = Tle.from_string(
                tle1=res['tle1'],
                tle2=res['tle2']
            )
            return tle
        else:
            # satellite tle not found
            return None

def save_TLE_data(url=None):
    tle_data = parse_tles_from_celestrak(url)
    with open('tle_data.json', 'w') as file:
        json.dump(tle_data, file)
