from logging import getLogger

from hatchet_sdk import Hatchet, ClientConfig

from api.settings import config


root_logger = getLogger()

hatchet = Hatchet(
    debug=config.debug,
    config=ClientConfig(
        logger=root_logger,
        token=config.hatchet.token.get_secret_value(),
        tls_config=config.hatchet.tls,
    )
)


__all__ = ["hatchet"]