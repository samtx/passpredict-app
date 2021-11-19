from datetime import date
import logging
import typing
import asyncio
import sys
import io
import csv
from collections import defaultdict, Counter, deque
import functools
from enum import Enum

from sqlalchemy import select, insert
from databases import Database
import httpx
import click
from tqdm.asyncio import tqdm

from app.dbmodels import (
    satellite as sat_model,
    satellite_status as sat_status_model,
    satellite_owner as sat_owner_model,
    satellite_type as sat_type_model,
    launch_site as site_model,
)

from app.resources import postgres_uri


logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


celestrak_data_headers = {
    "OBJECT_NAME",
	"OBJECT_ID",
    "NORAD_CAT_ID",
    "OBJECT_TYPE",
    "OPS_STATUS_CODE",
    "OWNER",
    "LAUNCH_DATE",
    "LAUNCH_SITE",
    "DECAY_DATE",
    "PERIOD",
    "INCLINATION",
    "APOGEE",
    "PERIGEE",
    "RCS",
    "DATA_STATUS_CODE",
    "ORBIT_CENTER",
    "ORBIT_TYPE",
}


class UpdateAction(Enum):
    INSERT = 1
    UPDATE = 2
    SKIP = 3


class SatelliteForeignKeys:
    _launch_site = defaultdict()
    _owner = defaultdict()
    _status = defaultdict()
    _type = defaultdict()

    def get_foreign_key_data(self):
        """
        Query database for foreign key data
        """
        asyncio.run(self.query_db())

    async def query_db(self):
        async with Database(postgres_uri) as conn:
            # Launch Sites
            query = select(site_model.c.id, site_model.c.short_name)
            rows = await conn.fetch_all(query=query)
            for r in rows:
                self._launch_site[r['short_name']] = int(r['id'])
            # Types
            query = select(sat_type_model.c.id, sat_type_model.c.short_name)
            rows = await conn.fetch_all(query=query)
            for r in rows:
                self._type[r['short_name']] = int(r['id'])
            # Status
            query = select(sat_status_model.c.id, sat_status_model.c.short_name)
            rows = await conn.fetch_all(query=query)
            for r in rows:
                self._status[r['short_name']] = int(r['id'])
            # Owner
            query = select(sat_owner_model.c.id, sat_owner_model.c.name)
            rows = await conn.fetch_all(query=query)
            for r in rows:
                self._owner[r['short_name']] = int(r['id'])

    def status(self, short_name: str):
        return self._status.get(short_name)

    def launch_site(self, short_name: str):
        return self._launch_site.get(short_name)

    def type(self, short_name: str):
        return self._type.get(short_name)

    def owner(self, short_name: str):
        return self._owner.get(short_name)


class Satellite(typing.NamedTuple):
    id: int
    name: str
    cospar_id: str
    decayed: bool
    launch_date: date
    launch_year: int
    launch_site_id: int
    decay_date: date
    period: float
    apogee: float
    inclination: float
    perigee: float
    owner_id: int
    status_id: int
    type_id: int
    rcs: float

    @classmethod
    def from_celestrak_data(cls, celestrak_data: dict, fk: SatelliteForeignKeys):
        """ Create instance from Celestrak data dictionary """
        data = defaultdict()
        data['id'] = int(celestrak_data['NORAD_CAT_ID'])
        if not data['id']:
            return None
        data['cospar_id'] = celestrak_data['OBJECT_ID']
        data['name'] = celestrak_data['OBJECT_NAME']
        data['launch_date'] = _parse_date_string(celestrak_data['LAUNCH_DATE'])
        launch_date = data['launch_date']
        data['launch_year'] = launch_date.year if launch_date else None
        data['decay_date'] = _parse_date_string(celestrak_data['DECAY_DATE'])
        data['period'] = _float_or_none(celestrak_data['PERIOD'])
        data['inclination'] = _float_or_none(celestrak_data['INCLINATION'])
        data['apogee'] = _float_or_none(celestrak_data['APOGEE'])
        data['perigee'] = _float_or_none(celestrak_data['PERIGEE'])
        data['rcs'] = _float_or_none(celestrak_data['RCS'])
        data['launch_site_id'] = fk.launch_site(celestrak_data['LAUNCH_SITE'])
        data['owner_id'] = fk.owner(celestrak_data['OWNER'])
        data['status_id'] = fk.status(celestrak_data['OPS_STATUS_CODE'])
        # check if status is 'D' for decayed
        if data['decay_date']:
            data['decayed'] = True
        else:
            data['decayed'] = False
        data['type_id'] = fk.type(celestrak_data['LAUNCH_SITE'])
        return cls(**data)


def _float_or_none(x: str):
    if x:
        return float(x)
    else:
        return None


def _parse_date_string(date_str):
    """ Create date object from string or else return None """
    if date_str:
        return date.fromisoformat(date_str)
    return None


def fetch(url, base_url=''):
    """
    fetch url from celestrak
    """
    headers = {'user-agent': 'passpredict.com'}
    with httpx.Client(base_url=base_url, headers=headers) as client:
        res = client.get(url)
    if not res:
        logger.error(f'Error downloading URL: {res.url}')
    return res


def parse_satellite_data(r: httpx.Response, fk: SatelliteForeignKeys) -> list[Satellite]:
    """
    Parse satellite data from satcat.csv from Celestrak

    satcat.csv example:
        OBJECT_NAME,OBJECT_ID,NORAD_CAT_ID,OBJECT_TYPE,OPS_STATUS_CODE,OWNER,LAUNCH_DATE,LAUNCH_SITE,DECAY_DATE,PERIOD,INCLINATION,APOGEE,PERIGEE,RCS,DATA_STATUS_CODE,ORBIT_CENTER,ORBIT_TYPE
        SL-1 R/B,1957-001A,1,R/B,D,CIS,1957-10-04,TYMSC,1957-12-01,96.19,65.10,938,214,20.4200,,EA,IMP
        SPUTNIK 1,1957-001B,2,PAY,D,CIS,1957-10-04,TYMSC,1958-01-03,96.10,65.00,1080,64,,,EA,IMP
        SPUTNIK 2,1957-002A,3,PAY,D,CIS,1957-11-03,TYMSC,1958-04-14,103.74,65.33,1659,211,0.0800,,EA,IMP
        EXPLORER 1,1958-001A,4,PAY,D,US,1958-02-01,AFETR,1970-03-31,88.48,33.15,215,183,,,EA,IMP
        VANGUARD 1,1958-002B,5,PAY,,US,1958-03-17,AFETR,,132.74,34.25,3830,654,0.1220,,EA,ORB
    """
    satellites = deque()
    csvfile = io.StringIO(r.text)
    reader = csv.DictReader(csvfile)
    # Make sure the headers haven't changed
    assert set(reader.fieldnames) == celestrak_data_headers, "CSV file headers have changed"
    for row in reader:
        try:
            sat = Satellite.from_celestrak_data(row, fk)
        except Exception:
            logger.error(f'Error parsing satellite {row["id"]}')
            logger.error(f'Record data: {row}')
            raise
        satellites.append(sat)
    return satellites


def popleftn(q: deque, n: int=1) -> deque:
    """ Popleft the next n items """
    if n == 1:
        return q.popleft()
    q2 = deque()
    i = 0
    while (len(q) != 0) and (i < n):
        q2.append(q.popleft())
        i += 1
    return q2


async def update_database(satellites, **kw):
    #  Import Satellite data to databse
    chunk_size = 150
    all_results = deque()
    async with Database(postgres_uri) as conn:
        t = tqdm(total=len(satellites))
        while len(satellites) > 0:
            sats = popleftn(satellites, chunk_size)
            tasks = [update_satellite_in_database(conn, sat, **kw) for sat in sats]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
            t.update(len(sats))
        t.close()
    return all_results


async def update_satellite_in_database(conn, sat, update_all=False) -> int:
    """
    Update database with new satellite data
    """
    # check if satellite exists
    # if not then insert new satellite record
    query = sat_model.select().where(
        sat_model.c.id == sat.id
    )
    res = await conn.fetch_one(query=query)
    if not res:
        query = insert(sat_model).values(**sat._asdict())
        await conn.execute(query=query)
        logger.debug(f'Created new satellite record {sat.id} in db')
        return UpdateAction.INSERT

    logger.debug(f'Satellite {sat.id} already exists in db')

    if update_all:
        # update entire record in database
        data = sat._asdict()
        del data['id']
        query = sat_model.update()  \
            .where(sat_model.c.id == sat.id)  \
            .values(**data)
        await conn.execute(query=query)
        logger.debug(f'Satellite {sat.id} is updated.')
        return UpdateAction.UPDATE

    # check if satellite record needs to be updated
    if res['decayed']:
        # if satellite has already been listed as decayed, then skip
        logger.debug(f'Satellite {sat.id} is already decayed. Skipping.')
        return UpdateAction.SKIP

    if (not res['decayed'] and sat.decayed) or (res['status_id'] != sat.status_id):
        # satellite status has recently changed, update the database with new info
        data = {
            'decayed': sat.decayed,
            'decay_date': sat.decay_date,
            'status_id': sat.status_id,
        }
        query = sat_model.update()  \
            .where(sat_model.c.id == sat.id)  \
            .values(**data)
        await conn.execute(query=query)
        logger.debug(f'Satellite {sat.id} is updated with new status.')
        return UpdateAction.UPDATE

    logger.debug(f'Satellite {sat.id} is not changed.')
    return UpdateAction.SKIP


@click.command()
@click.option('--debug', is_flag=True, default=False)
@click.option('--update-all', is_flag=True, default=False)
def main(debug, update_all):
    """
    Entrypoint for downloading, parsing, and updating Satellite database
    """
    if debug:
        logger.setLevel(logging.DEBUG)
    logger.info('Download satellite data from Celestrak')
    resp = fetch('https://celestrak.com/pub/satcat.csv')
    if not resp:
        logger.error(f'Error downloading data from {resp.url}')
        return

    # Get foreign key data from database
    sat_fk = SatelliteForeignKeys()
    sat_fk.get_foreign_key_data()

    # Parse satellite data
    try:
        satellites = parse_satellite_data(resp, sat_fk)
    except Exception:
        logger.error(f'Error parsing satellites from {resp.url}')
        return
    del resp
    n_satellites = len(satellites)
    logger.info(f"Total unique satellites found: {n_satellites}")

    # Update satellite database
    results = asyncio.run(update_database(satellites, update_all=update_all))
    for r in results:
        if isinstance(r, Exception):
            logger.error(r)

    # Display results
    counter = Counter(results)
    logger.info(f'Finished updating satellite database.')
    total = functools.reduce(lambda tot, k: tot + counter[k], counter.keys(), 0)
    if total != n_satellites:
        logger.info(f'Warning: Counter totals don\'t match: counter total = {total}')
    logger.info(f'Inserted {counter[UpdateAction.INSERT]:6d}')
    logger.info(f'Updated  {counter[UpdateAction.UPDATE]:6d}')
    logger.info(f'Skipped  {counter[UpdateAction.SKIP]:6d}')


if __name__ == "__main__":
    main()