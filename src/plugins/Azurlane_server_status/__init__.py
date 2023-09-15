#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json

import apscheduler
import nonebot
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from nonebot import on_metaevent
from nonebot.adapters.onebot.v11 import LifecycleMetaEvent
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.onebot.v11 import Bot
from .config import DATA_PATH, DATA_FILE, config

VERSION = "0.1.0"
__plugin_meta__ = PluginMetadata(
    name="Azurlane_server_status",
    description="QQ机器人 RSS订阅 插件，订阅源建议选择 RSSHub",
    usage="https://github.com/Quan666/ELF_RSS",
    extra={"author": "Quan666 <i@Rori.eMail>", "version": VERSION},
)

"""
官服:
http://118.178.152.242/?cmd=load_server?
日服:
http://18.179.191.97/?cmd=load_server?
渠道服:
http://203.107.54.70/?cmd=load_server?
苹果:
http://101.37.104.227/?cmd=load_server?
all_status = {
    0: "已开启",
    1: "未开启",
    2: "爆满",
    3: "已满",
}
"""


async def get_server_ip(server_name: str):
    """
    获取服务器IP
    :param server_name:
    :return:
    """
    if server_name == "日服":
        return "http://18.179.191.97/?cmd=load_server?"
    elif server_name in ["官服", "B服", "bilibili"]:
        return "http://118.178.152.242/?cmd=load_server?"
    elif server_name == "渠道服":
        return "http://203.107.54.70/?cmd=load_server?"
    elif server_name in ["ios", "苹果"]:
        return "http://101.37.104.227/?cmd=load_server?"
    else:
        msg = "不存在该服务器， 目前支持的服务器有：日服、官服(B服/bilibili)、渠道服、ios(苹果)"
        # await report_error(msg)
        raise Exception(msg)


async def get_server_status(sever_name: str):
    """
    获取服务器状态
    :return:
    """
    is_open = False
    async with httpx.AsyncClient() as client:
        res = await client.get(await get_server_ip(sever_name))
        for i in res.json():
            if i["state"] == 0:
                is_open = True
            elif i["state"] == 1:
                is_open = False
        return is_open


async def set_tigger():
    """
    设置定时器
    :return:
    """
    is_open = await get_server_status()
    if is_open:
        # 制作一个整点触发器
        trigger = CronTrigger(minute=0, hour="*", day="*", month="*")
    else:
        # 制作一个"5分钟/次"触发器
        trigger = CronTrigger(minute="0/5", hour="*", day="*", month="*")


def check_first_connect(_: LifecycleMetaEvent) -> bool:
    return True


start_metaevent = on_metaevent(rule=check_first_connect, temp=True)


@start_metaevent.handle()
async def __init__():
    status_dict = {}
    for i in ["官服", "苹果", "渠道服"]:
        status_dict[i] = await get_server_status(i)
    if not DATA_PATH.exists():
        DATA_PATH.mkdir(parents=True)
    with open(DATA_FILE.__str__(), "w+", encoding="utf-8") as f:
        f.write(json.dumps(status_dict, ensure_ascii=False))
    trigger = None
    x = True
    for i, j in status_dict.items():
        if j:
            x = True
        else:
            x = False
    if x:
        # 制作一个整点触发器
        trigger = CronTrigger(minute=0, hour="*", day="*", month="*")
        # trigger = CronTrigger(second="0/5", minute="*", hour="*", day="*", month="*")
        # trigger = IntervalTrigger(seconds=1)
        logger.info("【Azurlane_server_status】碧蓝航线服务器状态监控定时任务添加成功！每1小时触发1次！")
    else:
        # 制作一个"2分钟/次"触发器
        trigger = CronTrigger(minute="0/2", hour="*", day="*", month="*")
        logger.info("【Azurlane_server_status】碧蓝航线服务器状态监控定时任务添加成功！每2分钟触发1次！")
    scheduler.add_job(
        func=run_job,  # 要添加任务的函数，不要带参数
        trigger=trigger,  # 触发器
        id="国服",
        args=(),  # 函数的参数列表，注意：只有一个值时，不能省略末尾的逗号
        misfire_grace_time=30,  # 允许的误差时间，建议不要省略
        max_instances=10,  # 最大并发
        default=ThreadPoolExecutor(64),  # 最大线程
        processpool=ProcessPoolExecutor(8),  # 最大进程
        coalesce=True,  # 积攒的任务是否只跑一次，是否合并所有错过的Job
    )


async def run_job():
    with open(DATA_FILE, "r+", encoding="utf-8") as f:
        old_status = json.loads(f.read())
    new_status_dict = {}
    for i in ["官服", "苹果", "渠道服"]:
        new_status_dict[i] = await get_server_status(i)
    if not old_status == new_status_dict:
        trigger = None
        if list(new_status_dict.values()) == [True, True, True]:
            x = True
        else:
            x = False
        if x:
            # 制作一个整点触发器
            trigger = CronTrigger(minute="0", hour="*", day="*", month="*")
            logger.info("【Azurlane_server_status】触发器修改为每1小时触发1次！")
        else:
            # 制作一个"2分钟/次"触发器
            trigger = CronTrigger(minute="0/2", hour="*", day="*", month="*")
            logger.info("【Azurlane_server_status】触发器修改为每2分钟触发1次！")
        try:
            # 修改任务
            scheduler.reschedule_job(job_id="国服", trigger=trigger)
        except apscheduler.jobstores.base.JobLookupError as e:
            logger.warning(e)
        msg = "【碧蓝航线】服务器状态\n"
        s = False
        for i, j in new_status_dict.items():
            if j:
                msg += f"{i}开服啦！\n"
                s = True
        if s:
            bot = nonebot.get_bot()
            for n in config.az_group:
                await bot.send_msg(
                    group_id=n,
                    message=msg,
                )
        with open(DATA_FILE, "w+", encoding="utf-8") as f:
            f.write(json.dumps(new_status_dict, ensure_ascii=False))
        logger.info(f"【Azurlane_server_status】{msg}")
    logger.info("【Azurlane_server_status】碧蓝航线服务器状态监控运行中！")


if __name__ == '__main__':

    # 运行异步调度器
    scheduler.start()

    # 使用 asyncio 事件循环运行异步任务
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
        scheduler.print_jobs()
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.shutdown()
        loop.close()

    # scheduler.remove_job("test")
