import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from itertools import zip_longest
import logging
from itertools import chain, batched
from typing import cast, Awaitable, Any

import click
from databases import Database
import httpx
from sqlalchemy import and_
from hatchet_sdk import Context, ConcurrencyExpression, ConcurrencyLimitStrategy

from api.satellites.domain import SatelliteOrbit
from api.satellites.services import SatelliteService
from ..client import hatchet


logger = logging.getLogger(__name__)


DEFAULT_CELESTRAK_BASE_URL = "https://www.celestrak.com/NORAD/elements/gp.php"
DEFAULT_CELESTRAK_GROUPS = (
    'stations',
    'active',
    'visual',
    'amateur',
    'starlink',
    'last-30-days',
    'noaa',
    'goes',
)


@hatchet.workflow(on_crons=["17 */8 * * *"])
class FetchCelestrakOrbits:

    def __init__(
        self,
        *,
        db_conn,
        celestrak_base_url: str = DEFAULT_CELESTRAK_BASE_URL,
        celestrak_groups = DEFAULT_CELESTRAK_GROUPS,
        upsert_batch: int = 100,
    ):
        self.db_conn = db_conn
        self.celestrak_base_url = celestrak_base_url
        self.celestrak_groups = celestrak_groups
        self.upsert_batch = upsert_batch

    @hatchet.step()
    async def download_orbit_data(self, context: Context):
        """Async fetch orbit data from celestrak"""
        headers = {'user-agent': 'passpredict.com'}
        param_list = [
            {
                'GROUP': group,
                'FORMAT': 'JSON',
            }
            for group in self.celestrak_groups
        ]
        tasks = cast(list[Awaitable[httpx.Response]], [])
        queried_at = datetime.now(UTC)
        async with httpx.AsyncClient(base_url=self.celestrak_base_url, headers=headers) as client:
            for params in param_list:
                task = asyncio.create_task(client.get("", params=params))
                tasks.append(task)
                await asyncio.sleep(0.1)  # throttle a bit
            responses = await asyncio.gather(*tasks, return_exceptions=True)
        orbit_data = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                # Log exception and continue
                context.log(
                    "Error downloading orbits from celestrak, "
                    f"group '{self.celestrak_groups[i]}', {str(response)}"
                )
                continue
            if response.status_code >= 400:
                # Log response error and continue
                context.log(
                    "Bad HTTP response downloading orbits from celestrak, "
                    f"group '{self.celestrak_groups[i]}', {response.text}"
                )
                continue
            try:
                data = response.json()
                orbit_data.append(data)
            except Exception as exc:
                # Log exception and continue
                context.log(
                    "Error parsing orbit response from celestrak, "
                    f"group '{self.celestrak_groups[i]}', {str(exc)}"
                )
                continue
        return {
            "orbit_data": orbit_data,
            "queried_at": queried_at.isoformat(),
        }

    @hatchet.step(parents=["download_orbit_data"])
    def parse_orbit_data(self, context: Context):
        orbit_data = cast(
            list[list[dict[str, Any]]],
            context.step_output("download_orbit_data")["orbit_data"],
        )
        unique_orbit_data = {
            tuple(sorted(orbit.items()))
            for orbit in chain.from_iterable(orbit_data)
        }
        return {"unique_orbit_data": list(unique_orbit_data)}

    @hatchet.step(parents=["download_orbit_data", "parse_orbit_data"])
    async def upsert_database(self, context: Context):
        unique_orbit_data = context.step_output("parse_orbit_data")["unique_orbit_data"]
        queried_at_str = context.step_output("download_orbit_data")["queried_at"]
        queried_at = datetime.fromisoformat(queried_at_str)
        # batch orbit updates and upsert synchronously
        for orbits in batched(unique_orbit_data, self.upsert_batch):
            upsert_workflow = await context.aio.spawn_workflow(
                "UpsertOrbitBatch",
                {"orbits": orbits},
            )
            result = await upsert_workflow.result()

@hatchet.workflow()
class UpsertOrbitBatch:

    def __init__(
        self,
        db_conn,
    ):
        self.db_conn = db_conn

    @hatchet.step()
    async def upsert_orbits(self, context: Context):
        async with self.db_conn.begin() as session:
            service = SatelliteService(Session=session)
            orbits = context.workflow_input()["orbits"]
            new_orbits = await service.batch_insert_orbits(orbits)
        new_orbit_summary = [
            {
                "id": orbit.id,
                "norad_id": orbit.norad_id,
                "epoch": orbit.epoch.isoformat(),
            }
            for orbit in new_orbits
        ]
        return {"new_orbits": new_orbit_summary}




def grouper(iterable, n, fillvalue=None):
    """From itertools recipes https://docs.python.org/3.7/library/itertools.html#itertools-recipes
    Collect data into fixed-length chunks or blocks
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def epoch_from_tle_datetime(epoch_string: str) -> datetime:
    """Return datetime object from tle epoch string"""
    epoch_year = int(epoch_string[0:2])
    if epoch_year < 57:
        epoch_year += 2000
    else:
        epoch_year += 1900
    epoch_day = float(epoch_string[2:])
    epoch_day, epoch_day_fraction = divmod(epoch_day, 1)
    epoch_microseconds = epoch_day_fraction * 24 * 60 * 60 * 1e6
    return datetime(epoch_year, month=1, day=1, tzinfo=UTC) + \
        timedelta(days=int(epoch_day-1)) + \
        timedelta(microseconds=int(epoch_microseconds)
    )


def epoch_from_tle(tle1: str) -> datetime:
    """Extract epoch as datetime from tle line 1"""
    epoch_string = tle1[18:32]
    return epoch_from_tle_datetime(epoch_string)


def satid_from_tle(tle1: str) -> int:
    """Extract satellite NORAD ID as int from tle line 1"""
    return int(tle1[2:7])


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
        hash_str = "".join((str(self.satid), self.tle1, self.tle2))
        return hash(hash_str)


async def fetch(group, base_url=''):
    """Async fetch url from celestrak"""
    headers = {'user-agent': 'passpredict.com'}
    params = {
        'GROUP': group,
        'FORMAT': 'TLE',
    }
    async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
        res = await client.get('', params=params)
    if not res:
        logger.error('Error downloading URL: %s', res.url)
    return res


def parse_tle_data(r: httpx.Response) -> typing.Set[Tle]:
    #  Parse TLE data from url responses and save them in a set object
    tles = set()
    try:
        for tle_strings in grouper(r.text.splitlines(), 3):
            tle = Tle.from_string(tle_strings[1], tle_strings[2])
            tles.add(tle)
    except:
        logger.exception('Error parsing tles from url %s', r.url)
    return tles


async def update_database(tles, created_at):
    #  Import TLE data to databse
    async with Database(postgres_uri) as conn:
        tasks = [update_tle_in_database(conn, tle, created_at) for tle in tles]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return results


async def update_tle_in_database(conn, tle, created_at) -> int:
    """Update database with new TLE data"""
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
        logger.debug('Created new satellite record %s in db', tle.satid)
    logger.debug('Satellite %s already exists in db', tle.satid)
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
        logger.debug('Inserted satellite %s TLE for epoch %s in db.', tle.satid, tle.epoch)
        return 1
    logger.debug('TLE for satid %s and epoch %s already exists. Skipping.', tle.satid, tle.epoch)
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
    base_url = 'https://www.celestrak.com/NORAD/elements/gp.php'
    endpoints = [
        'stations',
        'active',
        'visual',
        'amateur',
        'starlink',
        'last-30-days',
        'noaa',
        'goes',
    ]
    tasks = [fetch(u, base_url) for u in endpoints]
    coro = asyncio.gather(*tasks, return_exceptions=True)
    logger.info('Download data from Celestrak')
    responses = asyncio.run(coro, debug=debug)
    tles = set()
    for r in responses:
        if not r:
            logger.error('Error downloading data from %s', r.url)
            continue
        try:
            tmp = parse_tle_data(r)
            tles |= tmp
        except Exception:
            logger.error('Error parsing TLEs from %s', r.url, exc_info=True)
    logger.info("Total unique TLEs found: %d", len(tles))
    created_at = datetime.now(UTC)
    results = asyncio.run(update_database(tles, created_at))
    inserts = []
    for r in results:
        if isinstance(r, Exception):
            logger.error(r)
        else:
            inserts.append(r)
    num_inserted = sum(inserts)
    logger.info('TLEs inserted %d, skipped %d', num_inserted, len(tles)-num_inserted)
    num_deleted = asyncio.run(remove_old_tles_from_database())
    logger.info('Number TLEs deleted: %d', num_deleted)
    logger.info('Finished updating TLE database.')


if __name__ == "__main__":
    main()