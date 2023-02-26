#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Time    : 2022/12/11 18:15
# @Author  : 落雪
# @Site    : 
# @File    : log.py
# @Software: PyCharm

from datetime import datetime, timedelta
from configs.path_config import LOG_PATH
from loguru import logger as logger_
from nonebot.log import default_format, default_filter


logger = logger_


logger.add(
    LOG_PATH / f'{datetime.now().date()}.log',
    level='INFO',
    rotation='00:00',
    format=default_format,
    filter=default_filter,
    retention=timedelta(days=30))

logger.add(
    LOG_PATH / f'error_{datetime.now().date()}.log',
    level='ERROR',
    rotation='00:00',
    format=default_format,
    filter=default_filter,
    retention=timedelta(days=30))