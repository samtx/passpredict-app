from datetime import datetime, timedelta
import logging
import time
from pathlib import Path
import typing
import asyncio
from collections import namedtuple

from sqlalchemy import and_, create_engine
import httpx
from sqlalchemy.sql.expression import update

# import os, sys
# print('sys.path',sys.path)
# print('sys.modules.keys()', sys.modules.keys())

from app.utils import grouper
from app.schemas import Tle
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

# Create synchronous DB engine connect
engine = create_engine(postgres_uri, echo=False)


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


def update_database(tles):
    #  Import TLE data to databse
    num_inserted = 0
    created_at = datetime.utcnow()
    with engine.connect() as conn:
        for tle in tles:
            try:
                res = update_tle_in_database(conn, tle, created_at)
                num_inserted += res
            except Exception as e:
                logger.exception('Exception trying to update database with new TLEs', exc_info=e)
                print('exception here!!', e, tle)
    num_skipped = len(tles) - num_inserted
    return (num_inserted, num_skipped)


def update_tle_in_database(conn, tle, created_at) -> int:
    """
    Update database with new TLE data
    """
    # check if satellite exists
    # if not then insert new satellite record
    stmt = satellite.select().where(
        satellite.c.id == tle.satid
    )
    res = conn.execute(stmt).fetchone()
    if not res:
        stmt = satellite.insert({
            'id': tle.satid
        })
        res = conn.execute(stmt)
        logger.debug(f'Created new satellite record {tle.satid} in db')

    # Check if there is a tle for the datetime,
    # if not then insert record, otherwise skip
    stmt = tledb.select().where(
        and_(
            tledb.c.satellite_id == tle.satid,
            tledb.c.epoch == tle.epoch
        )
    )
    res = conn.execute(stmt).fetchall()
    if not res:
        stmt = tledb.insert({
            'satellite_id': tle.satid,
            'tle1': tle.tle1,
            'tle2': tle.tle2,
            'epoch': tle.epoch,
            'created': created_at
        })
        res = conn.execute(stmt)
        logger.debug(f'Inserted satellite {tle.satid} TLE for epoch {tle.epoch} in db.')
        return 1
    return 0


def remove_old_tles_from_database() -> int:
    st = 'Remove old TLEs from database'
    logger.info(st)
    print(st)
    date_limit = datetime.utcnow() - timedelta(days=2)
    tles_deleted = 0
    with engine.connect() as conn:
        stmt = tledb.delete().where(
            tledb.c.epoch < date_limit
        )
        res = conn.execute(stmt)
        tles_deleted = res.rowcount
        print('done')
    return tles_deleted


def main():
    responses = download_tle_data()
    for r in responses:
        print(f'URL: {r.url}')
        if not r:
            logger.error(f'url {r.url} not downloaded, error code {r.status_code}')
        tles = parse_tle_data(r)
        num_inserted, num_skipped = update_database(tles)
        st = f'Url: {r.url}, inserted {num_inserted}, skipped {num_skipped}'
        logger.info(st)
        print(st)

    num_deleted = remove_old_tles_from_database()
    print(f'Number TLEs deleted: {num_deleted}')

    logger.info(f'Finishe d updating TLE database.')
    print(f'Finished updating TLE database.')


if __name__ == "__main__":
    main()