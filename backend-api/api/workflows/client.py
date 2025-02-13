import logging

from hatchet_sdk import Hatchet, ClientConfig


root_logger = logging.getLogger()



hatchet = Hatchet(
    config=ClientConfig(
        logger=root_logger,
    )
)


__all__ = ["hatchet"]