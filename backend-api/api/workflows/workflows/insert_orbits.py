import logging
from typing import Any

from hatchet_sdk import Context
from sqlalchemy.ext.asyncio import async_sessionmaker

from api.satellites.services import SatelliteService
from api.satellites.domain import Orbit, Satellite
from ..client import hatchet


__all__ = [
    "InsertOrbitBatch",
]


logger = logging.getLogger(__name__)


@hatchet.workflow()
class InsertOrbitBatch:

    def __init__(
        self,
        WriteSession: async_sessionmaker,
    ):
        self.WriteSession = WriteSession

    @hatchet.step()
    async def insert_orbits(self, context: Context) -> dict[str, Any]:
        input_ = context.workflow_input()
        orbits = input_["orbits"]
        async with self.WriteSession.begin() as session:
            service = SatelliteService(session)
            new_orbits = await service.batch_insert_orbits(orbits)
        new_orbit_summary = [
            {
                "id": str(orbit.id),
                "norad_id": orbit.norad_id,
                "epoch": orbit.epoch.isoformat(),
                "originator": orbit.originator,
            }
            for orbit in new_orbits
        ]
        return {"new_orbits": new_orbit_summary}
