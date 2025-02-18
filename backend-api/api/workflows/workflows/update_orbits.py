import asyncio
from datetime import datetime, UTC
import logging
from itertools import chain, batched
from typing import cast, Awaitable, Any

import httpx
from hatchet_sdk import Context
from sqlalchemy.ext.asyncio import async_sessionmaker

from api.satellites.services import SatelliteService
from ..client import hatchet


__all__ = [
    "FetchCelestrakOrbits",
    "InsertOrbitBatch",
]


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
        celestrak_base_url: str = DEFAULT_CELESTRAK_BASE_URL,
        celestrak_groups = DEFAULT_CELESTRAK_GROUPS,
        batch_count: int = 100,
    ):
        self.celestrak_base_url = celestrak_base_url
        self.celestrak_groups = celestrak_groups
        self.batch_count = batch_count

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
    async def insert_orbits_to_database(self, context: Context):
        unique_orbit_data = context.step_output("parse_orbit_data")["unique_orbit_data"]
        queried_at = context.step_output("download_orbit_data")["queried_at"]
        # batch orbit updates and insert synchronously
        results = {"new_orbits": []}
        for orbits in batched(unique_orbit_data, self.batch_count):
            insert_workflow = await context.aio.spawn_workflow(
                "InsertOrbitBatch",
                {
                    "orbits": orbits,
                    "queried_at": queried_at,
                },
            )
            workflow_result = await insert_workflow.result()
            results["new_orbits"].extend(workflow_result["new_orbits"])
        return results


@hatchet.workflow()
class InsertOrbitBatch:

    def __init__(
        self,
        WriteSession: async_sessionmaker,
    ):
        self.WriteSession = WriteSession

    @hatchet.step()
    async def insert_orbits(self, context: Context) -> dict[str, Any]:
        orbits = context.workflow_input()["orbits"]
        async with self.WriteSession.begin() as session:
            service = SatelliteService(session)
            new_orbits = await service.batch_insert_orbits(orbits)
        new_orbit_summary = [
            {
                "id": orbit.id,
                "norad_id": orbit.norad_id,
                "epoch": orbit.epoch.isoformat(),
                "originator": orbit.originator,
            }
            for orbit in new_orbits
        ]
        return {"new_orbits": new_orbit_summary}
