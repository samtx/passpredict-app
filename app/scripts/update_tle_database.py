from datetime import datetime, timedelta
import logging
import typing
import asyncio
import sys
from collections import namedtuple
from dataclasses import dataclass

from sqlalchemy import and_
from databases import Database
import httpx
import click
from tqdm.asyncio import tqdm

from app.utils import grouper, epoch_from_tle, satid_from_tle
from app.dbmodels import satellite, tle as tledb
from app.resources import postgres_uri


logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


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
    logger.info('Download TLEs from Celestrak')
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
    if not res:
        logger.error(f'Error downloading URL: {res.url}')
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
    async with Database(postgres_uri) as conn:
        tasks = [update_tle_in_database(conn, tle, created_at) for tle in tles]
        results = await tqdm.gather(*tasks)
    return results


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
    logger.debug(f'Satellite {tle.satid} already exists in db')
    # Check if there is a tle for the datetime,
    # if not then insert record, otherwise skip
    query = tledb.select().where(
        and_(
            tledb.c.satellite_id == tle.satid,
            tledb.c.epoch == tle.epoch
        )
    )
    res = await conn.fetch_one(query=query)
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
    logger.debug(f'TLE for satid {tle.satid} and epoch {tle.epoch} already exists. Skipping.')
    return 0


async def remove_old_tles_from_database() -> int:
    logger.info('Remove old TLEs from database')
    date_limit = datetime.utcnow() - timedelta(days=2)
    tles_deleted = 0
    async with Database(postgres_uri) as db:
        async with db.connection() as conn:
            rawconn = conn.raw_connection
            query = """DELETE FROM tle WHERE tle.epoch < ($1) RETURNING tle.id"""
            res = await rawconn.fetch(query, date_limit)
            try:
                tles_deleted = len(res)
            except TypeError:
                tles_deleted = 'Unknown'
    return tles_deleted

@click.command()
@click.option('--debug', is_flag=True, default=False)
def main(debug):
    """
    Entrypoint for downloading, parsing, and updating TLE database
    """
    if debug:
        logger.setLevel(logging.DEBUG)
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
    logger.info('Download data from Celestrak')
    responses = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    created_at = datetime.utcnow()
    tles = set()
    for r in responses:
        if not r:
            logger.error(f'Error downloading data from {r.url}')
            continue
        try:
            tmp = parse_tle_data(r)
            tles |= tmp
        except:
            logger.error(f'Error parsing TLEs from {r.url}')
    logger.info(f"Total unique TLEs found: {len(tles)}")
    results = asyncio.run(update_database(tles, created_at))
    inserts = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(r)
        else:
            inserts.append(r)
    num_inserted = sum(inserts)
    num_skipped = len(tles) - num_inserted
    logger.info(f'TLEs inserted {num_inserted}, skipped {num_skipped}')
    num_deleted = asyncio.run(remove_old_tles_from_database())
    logger.info(f'Number TLEs deleted: {num_deleted}')
    logger.info(f'Finished updating TLE database.')


if __name__ == "__main__":
    main()