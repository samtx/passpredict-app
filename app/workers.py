from uvicorn.workers import UvicornWorker as UvicornWorkerBase

class UvicornWorker(UvicornWorkerBase):
    CONFIG_KWARGS = {
        "proxy-headers": True,
    }