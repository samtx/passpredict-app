# TLE source for web app
import datetime
from typing import NamedTuple, Tuple

from app.astrodynamics import AsyncPasspredictTLESource, SGP4Predictor
from app.astrodynamics import TLE
from sqlalchemy import select
from starlette.exceptions import HTTPException
from databases import Database
from aioredis import Redis

from app.dbmodels import tle as tledb


class PasspredictTLESource(AsyncPasspredictTLESource):
    """
    TLE source that checks the redis cache and postgres database
    for orbital elements
    """

    def __init__(self, db: Database, cache: Redis):
        self.db = db
        self.cache = cache

    async def add_tle(self, satid, tle):
        """
        Add TLE to cache
        """
        key = self.tle_cache_key(satid)
        data = "\n".join(tle.lines).encode('utf-8')
        await self.cache.set(key, data, ex=10)  # save for 10 seconds

    async def get_tle_or_404(self, satid: int, date: datetime.datetime):
        """
        Get TLE from source object
        Raise 404 error if TLE not found in database
        """
        # First check cache
        tle = await self.check_cache(satid, date)
        if tle:
            return tle
        # Then check database
        tle = await self.check_db(satid, date)
        if tle:
            # Make this a background task
            await self.add_tle(satid, tle)
            # return tle
            return tle
        raise HTTPException(status_code=404, detail=f'TLE for satellite ID {satid} not found')


    def tle_cache_key(self, satid: int):
        """
        Generate string to use for redis cache key
        """
        key = f"tle:{satid}"
        return key

    async def check_cache(self, satid: int, date: datetime.datetime):
        """
        Check cache if TLE is already stored there
        """
        key = self.tle_cache_key(satid)
        result = await self.cache.get(key)
        if result:
            lines = result.decode('utf-8').splitlines()
            tle = TLE(satid, lines, date)
            return tle
        return None

    async def check_db(self, satid: int, date: datetime.datetime):
        """
        Check database if TLE is stored there
        """
        stmt = select(tledb).where(
            tledb.c.satellite_id == satid
        ).order_by(
            tledb.c.epoch.desc()
        )
        # stmt = select(
        #     subq.c.id,
        #     func.max(subq.c.epoch).label('latest')
        # ).join(
        #     subq, stmt.c.id == subq.c.id
        # )
        # stmt = select(tledb).join_from(subq, max_date)
        res = await self.db.fetch_one(query=stmt)
        if res:
            lines = (res['tle1'], res['tle2'])
            tle = TLE(satid, lines, res['epoch'])
            return tle
        return None

    async def get_predictor(self, satid: int, date: datetime.datetime):
        """
        Create Predictor instance with TLE data
        """
        tle = await self.get_tle_or_404(satid, date)
        satellite = SGP4Predictor.from_tle(tle)
        return satellite
