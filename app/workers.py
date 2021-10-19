import socket

from uvicorn.workers import UvicornWorker as UvicornWorkerBase

# import Arq job functions
# from app.scripts import update_tle_database
from app.resources import queue_settings
from app.core.jobs import (
    set_cache_with_pickle,
    update_tle_database,
)

docker_host = socket.gethostbyname('host.docker.internal')
forwarded_allow_ips = [docker_host] if docker_host else []


class UvicornWorker(UvicornWorkerBase):
    CONFIG_KWARGS = {
        "loop": "auto",
        "http": "auto",
        "proxy_headers": True,
        "forwarded_allow_ips": forwarded_allow_ips,
    }


class ArqWorkerSettings:
    functions = [
        set_cache_with_pickle,
        update_tle_database
    ]
    redis_settings = queue_settings


if __name__ == "__main__":
    # Run Arq worker from command line. Usefule for VSCode debugging
    from arq.cli import cli
    cli(ArqWorkerSettings)