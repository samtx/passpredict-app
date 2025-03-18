from hatchet_sdk import RateLimitDuration

from api.settings import config
from .client import hatchet
from .workflows import (
    FetchCelestrakOrbits,
    CelestrakOrbitRequest,
    FetchSpacetrackOrbits,
    InsertOrbitBatch,
)


def start():
    for fetch_config in (config.spacetrack.gp_fetch, config.spacetrack.satcat_fetch):
        hatchet.admin.put_rate_limit(
            fetch_config.key,
            fetch_config.limit,
            duration=fetch_config.duration,
        )
    worker = hatchet.worker(name="passpredict-api-worker")
    worker.register_workflow(FetchCelestrakOrbits())
    worker.register_workflow(CelestrakOrbitRequest())
    worker.register_workflow(FetchSpacetrackOrbits(
        username=config.spacetrack.username,
        password=config.spacetrack.password.get_secret_value(),
    ))
    sync_db_url = config.db.sqlalchemy_conn_url(sync=True)
    worker.register_workflow(InsertOrbitBatch(db_url=sync_db_url))
    worker.start()