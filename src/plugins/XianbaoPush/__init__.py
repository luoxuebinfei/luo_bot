import nonebot
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import MessageSegment
from .get_new_message import get_details_push, get_simple_push
from .config import config

n = 0


async def send_periodic_message():
    # 在这里编写你要执行的发送消息的逻辑
    # 可以调用 bot.send() 方法发送消息给用户
    # 例如：
    # user_id = 1732806519  # 替换为你要发送消息的用户的 QQ 号
    group_id_list = config.xianbao_group_id  # 替换为你要发送消息的群组的 QQ 号
    # messages = get_details_push()[::-1]
    messages = get_simple_push()[::-1]
    # try:
    if len(messages) != 0:
        for i in messages:
            if len(i) != 0:
                x = ""
                # x = x + i["title"] + "\n\n"
                # x += i["text"]
                # for j in i["images"]:
                #     x += f"[CQ:image,file={j}]"
                x = x + i
                try:
                    bot = nonebot.get_bot()
                    for group_id in group_id_list:
                        await bot.send_msg(
                            message=x,
                            group_id=group_id,
                        )
                except nonebot.adapters.onebot.v11.exception.ActionFailed as e:
                    logger.error("消息发送失败：账号可能被风控...")
    # except ValueError as e:
    #     print(e)


nonebot.require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

if config.xianbao_open:
    scheduler.add_job(send_periodic_message, "interval", seconds=15, id="send_periodic_message")