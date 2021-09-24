from uvicorn.workers import UvicornWorker as UvicornWorkerBase

class UvicornWorker(UvicornWorkerBase):
    CONFIG_KWARGS = {
        "loop": "auto",
        "http": "auto",
        "proxy_headers": True,
    }