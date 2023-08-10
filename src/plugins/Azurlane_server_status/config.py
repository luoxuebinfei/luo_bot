from pathlib import Path

from nonebot import get_driver, logger
from nonebot.config import BaseConfig

DATA_PATH = Path.cwd() / "data" / "Azurlane_server_status"
DATA_FILE = DATA_PATH / "AZ.json"


class AZConfig(BaseConfig):
    az_group: list = []


config = AZConfig(**get_driver().config.dict())
logger.debug(f"Azurlane_server_status Config loaded: {config!r}")
