from hatchet_sdk import RateLimitDuration

from api.settings import config
from api.db import WriteSession
from .client import hatchet
from .workflows import (
    FetchCelestrakOrbits,
    CelestrakOrbitRequest,
    FetchSpacetrackOrbits,
    InsertOrbitBatch,
)


def start():
    hatchet.admin.put_rate_limit("spacetrack-tle-request", 30, duration=RateLimitDuration.HOUR)
    worker = hatchet.worker(name="passpredict-api-worker")
    worker.register_workflow(FetchCelestrakOrbits())
    worker.register_workflow(CelestrakOrbitRequest())
    worker.register_workflow(FetchSpacetrackOrbits(
        username=config.spacetrack.username,
        password=config.spacetrack.password.get_secret_value(),
    ))
    worker.register_workflow(InsertOrbitBatch(WriteSession))
    worker.start()