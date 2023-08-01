from nonebot import get_driver
from nonebot.config import BaseConfig


class Config(BaseConfig):
    # 线报推送的开关
    xianbao_open: bool = False
    # 线报推送的群
    xianbao_group_id: list = []


config = Config(**get_driver().config.dict())
