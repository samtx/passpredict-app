from api.db import WriteSession
from .client import hatchet
from .workflows import FetchCelestrakOrbits, InsertOrbitBatch


def start():
    worker = hatchet.worker(
        name="passpredict-api-worker",
    )
    worker.register_workflow(FetchCelestrakOrbits())
    worker.register_workflow(InsertOrbitBatch(WriteSession))
    worker.start()
