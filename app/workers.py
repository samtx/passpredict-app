import socket

from uvicorn.workers import UvicornWorker as UvicornWorkerBase

docker_host = socket.gethostbyname('host.docker.internal')
forwarded_allow_ips = list(docker_host) if docker_host else []


class UvicornWorker(UvicornWorkerBase):
    CONFIG_KWARGS = {
        "loop": "auto",
        "http": "auto",
        "proxy_headers": True,
        "forwarded_allow_ips": forwarded_allow_ips,
    }