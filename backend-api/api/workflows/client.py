from logging import getLogger

from hatchet_sdk import Hatchet, ClientConfig


root_logger = getLogger()

hatchet = Hatchet(
    config=ClientConfig(
        logger=root_logger,
    )
)


__all__ = ["hatchet"]