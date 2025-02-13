from .client import hatchet
from .update_orbits import FetchCelestrakOrbits


def start():
    worker = hatchet.worker(
        name="passpredict-api-worker",
    )
    worker.register_workflow(FetchCelestrakOrbits())
    worker.start()
