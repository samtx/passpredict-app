from datetime import datetime, UTC
import logging
from itertools import chain, batched
from typing import cast, Any

import httpx
from hatchet_sdk import Context

from ..client import hatchet


__all__ = [
    "FetchCelestrakOrbits",
    "CelestrakOrbitRequest",
]


logger = logging.getLogger(__name__)


DEFAULT_CELESTRAK_BASE_URL = "https://celestrak.com/NORAD/elements/gp.php"
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
DEFAULT_CELESTRAK_TIMEOUT = 30
DEFAULT_SPACETRACK_BASE_URL = "https://www.space-track.org"
DEFAULT_SPACETRACK_TIMEOUT = 30
DEFAULT_SPACETRACK_EPOCH_DAYS_SINCE = 3


@hatchet.workflow(
    on_events=["fetch-orbits:celestrak"],
    on_crons=["17 2,10,18 * * *"],
)
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
        input_ = context.workflow_input()
        timeout = input_.get("timeout", DEFAULT_CELESTRAK_TIMEOUT)
        groups = input_.get("groups", DEFAULT_CELESTRAK_GROUPS)
        orbit_data = []
        for group in groups:
            request_workflow = await context.aio.spawn_workflow(
                "CelestrakOrbitRequest",
                {
                    "base_url": self.celestrak_base_url,
                    "endpoint": "",
                    "timeout": timeout,
                    "params": {
                        "GROUP": group,
                        "FORMAT": "JSON",
                    },
                },
            )
            workflow_result = await request_workflow.result()
            orbit_data.extend(workflow_result["orbit_data"])
        queried_at = datetime.now(UTC)
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
class CelestrakOrbitRequest:

    @hatchet.step(retries=3, backoff_factor=2)
    async def get_orbits(self, context: Context) -> dict[str, Any]:
        input_ = context.workflow_input()
        params = input_["params"]
        base_url = input_.get("base_url", DEFAULT_CELESTRAK_BASE_URL)
        endpoint = input_.get("endpoint", "")
        timeout = input_.get("timeout", DEFAULT_CELESTRAK_TIMEOUT)
        headers = {'user-agent': 'api.passpredict.com'}
        async with httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            try:
                response = await client.get(endpoint, params=params)
            except Exception as exc:
                context.log(
                    "HTTP request error downloading orbits from celestrak, "
                    f"group '{params["GROUP"]}', {repr(exc)}"
                )
                raise exc
        if response.status_code >= 400:
            # Log response error and return nothing
            context.log(
                "Bad HTTP response downloading orbits from celestrak, "
                f"group '{params["GROUP"]}', {response.text}"
            )
            return {}
        try:
            data = response.json()
        except Exception as exc:
            # Log exception and continue
            context.log(
                "Error parsing orbit response from celestrak, "
                f"group '{params["GROUP"]}', {str(exc)}, "
                f"text: {response.text}"
            )
            return {}
        return {"orbit_data": data}
