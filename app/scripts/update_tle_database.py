from datetime import datetime, timedelta
import logging
import time
from pathlib import Path

import requests
from sqlalchemy import and_

# import os, sys
# print('sys.path',sys.path)
# print('sys.modules.keys()', sys.modules.keys())

from app.utils import grouper
from app.schemas import Tle
from app.database import engine
from app.dbmodels import tle as tledb


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


#  Download common tle data from celestrak
st = 'Download TLEs from Celestrak'
logger.info(st)
print(st)
urls = [
    'https://www.celestrak.com/NORAD/elements/stations.txt',
    'https://www.celestrak.com/NORAD/elements/active.txt',
    'https://www.celestrak.com/NORAD/elements/visual.txt',
    'https://www.celestrak.com/NORAD/elements/amateur.txt',
    'https://www.celestrak.com/NORAD/elements/starlink.txt',
    'https://www.celestrak.com/NORAD/elements/tle-new.txt',
    'https://www.celestrak.com/NORAD/elements/noaa.txt',
    'https://www.celestrak.com/NORAD/elements/goes.txt',
    'https://celestrak.com/NORAD/elements/supplemental/starlink.txt',
    'https://celestrak.com/NORAD/elements/supplemental/planet.txt',
]

for url in urls:
    r = requests.get(url)
    logger.info(f'request url {url}')
    print('url ', url)
    if r.status_code != 200:
        logger.error(f'url {url} not downloaded, error code {r.status_code}')
        continue

    #  Parse TLE data from url responses and save them in a set object
    tles = set()
    try:
        for tle_strings in grouper(r.text.splitlines(), 3):
            tle = Tle.from_string(tle_strings[1], tle_strings[2])
            tles.add(tle)
    except:
        logger.exception(f'Error parsing tles from url {r.url}')

    #  Import TLE data to databse
    num_inserted, num_skipped = 0, 0
    created_at = datetime.utcnow()
    conn = engine.connect()
    for tle in tles:
        try:
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
                # print(f'Inserted satellite {tle.satid} TLE for epoch {tle.epoch} in db.')
                num_inserted += 1
            else:
                logger.debug(f'Sat {tle.satid} for epoch {tle.epoch} already exists in db. Skipping...')
                # print(f'Sat {tle.satid} for epoch {tle.epoch} already exists in db. Skipping...')
                num_skipped += 1
        except Exception as e:
            logger.exception('Exception trying to update database with new TLEs', exc_info=e)
            print('exception here!!', e, tle)
    conn.close()
    st = f'Url: {url}, inserted {num_inserted}, skipped {num_skipped}'
    logger.info(st)
    print(st)
    time.sleep(2)   # wait 2 seconds to avoid hitting celestrak server too much

logger.info(f'Finished updating TLE database.')
print(f'Finished updating TLE database.')


# Remove old TLEs
st = 'Remove old TLEs from database'
logger.info(st)
print(st)
date_limit = datetime.utcnow() - timedelta(days=7)
tles_deleted = 0
with engine.connect() as conn:
    stmt = tledb.delete().where(
        tledb.c.epoch < date_limit
    )
    res = conn.execute(stmt)
    tles_deleted = res.rowcount
    print('done')
print(f'Number TLEs deleted: {tles_deleted}')