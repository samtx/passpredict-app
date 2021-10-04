from datetime import datetime, timedelta
import logging
import time
from pathlib import Path
import typing
import asyncio
from collections import namedtuple
from dataclasses import dataclass
import functools

from sqlalchemy import and_, create_engine
from databases import Database
import httpx
from sqlalchemy.sql.expression import update

# import os, sys
# print('sys.path',sys.path)
# print('sys.modules.keys()', sys.modules.keys())

from app.utils import grouper, epoch_from_tle, satid_from_tle
from app.dbmodels import satellite, tle as tledb
from app.resources import postgres_uri


log_path = Path(__file__).parent.parent
log_filename = log_path / "update-tle.log"
logging.basicConfig(
    filename=log_filename,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# # Create handlers
# fh = logging.FileHandler('app-update-tle.log')
# fh.setLevel(logging.DEBUG)
# logger.addHandler(fh)


@dataclass
class Tle:
    tle1: str
    tle2: str
    epoch: datetime
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



def download_tle_data():
    """
    Download common tle data from celestrak
    """

    st = 'Download TLEs from Celestrak'
    logger.info(st)
    print(st)
    base_url = 'https://www.celestrak.com/NORAD/elements/'
    endpoints = [
        'stations.txt',
        'active.txt',
        'visual.txt',
        'amateur.txt',
        'starlink.txt',
        'tle-new.txt',
        'noaa.txt',
        'goes.txt',
        'supplemental/starlink.txt',
        'supplemental/planet.txt',
    ]
    tasks = [fetch(u, base_url) for u in endpoints]
    loop = asyncio.get_event_loop()
    responses = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    return responses


async def fetch(url, base_url=''):
    """
    Async fetch url from celestrak
    """
    headers = {'user-agent': 'passpredict.com'}
    async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
        res = await client.get(url)
    return res


def parse_tle_data(r: httpx.Response) -> typing.Set[Tle]:
    #  Parse TLE data from url responses and save them in a set object
    tles = set()
    try:
        for tle_strings in grouper(r.text.splitlines(), 3):
            tle = Tle.from_string(tle_strings[1], tle_strings[2])
            tles.add(tle)
    except:
        logger.exception(f'Error parsing tles from url {r.url}')
    return tles


async def update_database(tles, created_at):
    #  Import TLE data to databse
    num_inserted = 0
    async with Database(postgres_uri) as conn:
        tasks = [update_tle_in_database(conn, tle, created_at) for tle in tles]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    num_inserted = sum(results)
    num_skipped = len(tles) - num_inserted
    return (num_inserted, num_skipped)


async def update_tle_in_database(conn, tle, created_at) -> int:
    """
    Update database with new TLE data
    """
    # check if satellite exists
    # if not then insert new satellite record
    query = satellite.select().where(
        satellite.c.id == tle.satid
    )
    res = await conn.fetch_one(query=query)
    if not res:
        query = satellite.insert({
            'id': tle.satid
        })
        res = await conn.execute(query=query)
        logger.debug(f'Created new satellite record {tle.satid} in db')

    # Check if there is a tle for the datetime,
    # if not then insert record, otherwise skip
    query = tledb.select().where(
        and_(
            tledb.c.satellite_id == tle.satid,
            tledb.c.epoch == tle.epoch
        )
    )
    res = await conn.fetch_all(query=query)
    if not res:
        stmt = tledb.insert({
            'satellite_id': tle.satid,
            'tle1': tle.tle1,
            'tle2': tle.tle2,
            'epoch': tle.epoch,
            'created': created_at
        })
        res = await conn.execute(stmt)
        logger.debug(f'Inserted satellite {tle.satid} TLE for epoch {tle.epoch} in db.')
        return 1
    return 0


async def remove_old_tles_from_database() -> int:
    st = 'Remove old TLEs from database'
    logger.info(st)
    print(st)
    date_limit = datetime.utcnow() - timedelta(days=2)
    tles_deleted = 0
    async with Database(postgres_uri) as conn:
        stmt = tledb.delete().where(
            tledb.c.epoch < date_limit
        )
        res = await conn.fetch_all(stmt)
        tles_deleted = sum(res)
        print('done')
    return tles_deleted


def main():
    """
    Entrypoint for downloading, parsing, and updating TLE database
    """
    base_url = 'https://www.celestrak.com/NORAD/elements/'
    endpoints = [
        'stations.txt',
        'active.txt',
        'visual.txt',
        'amateur.txt',
        'starlink.txt',
        'tle-new.txt',
        'noaa.txt',
        'goes.txt',
        'supplemental/starlink.txt',
        'supplemental/planet.txt',
    ]
    tasks = [fetch(u, base_url) for u in endpoints]
    loop = asyncio.get_event_loop()
    responses = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    created_at = datetime.utcnow()
    for r in responses:
        print(f'URL: {r.url}')
        if not r:
            logger.error(f'url {r.url} not downloaded, error code {r.status_code}')
        tles = parse_tle_data(r)
        num_inserted, num_skipped = asyncio.run(update_database(tles, created_at))
        st = f'Url: {r.url}, inserted {num_inserted}, skipped {num_skipped}'
        logger.info(st)
        print(st)

    num_deleted = asyncio.run(remove_old_tles_from_database())
    print(f'Number TLEs deleted: {num_deleted}')

    logger.info(f'Finishe d updating TLE database.')
    print(f'Finished updating TLE database.')


if __name__ == "__main__":
    main()