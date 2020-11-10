from datetime import datetime
import logging
import time

import requests
from sqlalchemy.sql import select
from sqlalchemy import and_

from app.utils import grouper
from app.schemas import Tle
from app.database import engine
from app.dbmodels import tle as tledb

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

# Create handlers
fh = logging.FileHandler('passpredict-update-tle.log')
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(fmt)
fh.setLevel(logging.INFO)
logger.addHandler(fh)


#  Download common tle data from celestrak
urls = [
    'https://www.celestrak.com/NORAD/elements/active.txt',
    'https://www.celestrak.com/NORAD/elements/visual.txt',
    'https://www.celestrak.com/NORAD/elements/stations.txt',
    'https://www.celestrak.com/NORAD/elements/amateur.txt',
    'https://www.celestrak.com/NORAD/elements/starlink.txt',
    'https://www.celestrak.com/NORAD/elements/tle-new.txt',
    'https://www.celestrak.com/NORAD/elements/noaa.txt',
    'https://www.celestrak.com/NORAD/elements/goes.txt',

]
url_responses = []
for url in urls:
    r = requests.get(url)
    logger.info(f'request url {url}')
    if r.status_code != 200:
        logger.error(f'url {url} not downloaded, error code {r.status_code}')
        continue
    url_responses.append(r)
    time.sleep(2)   # wait 2 seconds to avoid hitting celestrak server too much

#  Parse TLE data from url responses and save them in a set object
tles = set()
for r in url_responses:
    try:
        for tle_strings in grouper(r.text.splitlines(), 3):
            tle = Tle.from_string(tle_strings[1], tle_strings[2])
            tles.add(tle)
    except Exception:
        logger.exception(f'Error parsing tles from url {r.url}')


#  Import TLE data to databse
num_inserted = 0
num_skipped = 0
created_at = datetime.utcnow()
try:
    conn = engine.connect()
    for tle in tles:
        # Check if there is a tle for the datetime, 
        # if not then insert record, otherwise skip
        stmt = select([tledb]).where(
            and_(
                tledb.c.satellite_id == tle.satid,
                tledb.c.epoch == tle.epoch
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
            logger.debug(f'Inserted satellite {tle.satid} TLE for epoch {tle.epoch} in db.')
            num_inserted += 1
        else:
            logger.debug(f'Sat {tle.satid} for epoch {tle.epoch} already exists in db. Skipping...')
            num_skipped += 1
except Exception:
    logger.exception('Exception trying to update database with new TLEs')
finally:
    conn.close()

logger.info(f'Finished updating TLE database. Inserted {num_inserted}, skipped {num_skipped}')
