import asyncio
import datetime
import re
from collections import defaultdict
from contextlib import suppress
from typing import DefaultDict, List, Optional, Tuple, Union

import arrow
from aiohttp import ClientSession
from diskcache import Cache
from nonebot.adapters.onebot.v11 import (
    ActionFailed,
    Bot,
    GroupMessageEvent,
    LifecycleMetaEvent,
    Message,
    MessageEvent,
    PrivateMessageEvent,
)
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.plugin.on import on_command, on_message, on_metaevent
from nonebot.rule import Rule
from PicImageSearch import Network
from tenacity import AsyncRetrying, stop_after_attempt, stop_after_delay

from .ascii2d import ascii2d_search
from .baidu import baidu_search
from .cache import exist_in_cache, upsert_cache
from .config import config
from .ehentai import ehentai_search
from .iqdb import iqdb_search
from .saucenao import saucenao_search
from .utils import DEFAULT_HEADERS, get_bot_friend_list, handle_img, handle_reply_msg

sending_lock: DefaultDict[Tuple[Union[int, str], str], asyncio.Lock] = defaultdict(
    asyncio.Lock
)


# issue #30 and #32 ?
# if sys.version_info >= (3, 8) and sys.platform == "win32":
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 已存在问题：cq中显示已发送，但私聊无法收到搜图结果
# 测试同样的内容在群聊中能够发送，无报错，产生原因不知

def check_first_connect(_: LifecycleMetaEvent) -> bool:
    return True


start_metaevent = on_metaevent(rule=check_first_connect, temp=True)


@start_metaevent.handle()
async def _(bot: Bot) -> None:
    if not config.saucenao_api_key:
        await bot.send_private_msg(
            user_id=int(list(config.superusers)[0]),
            message="请配置 saucenao_api_key ，否则无法正常使用搜图功能",
        )


# 消息中是否含有图片
def has_images(event: MessageEvent) -> bool:
    message = event.reply.message if event.reply else event.message
    return bool([i for i in message if i.type == "image"])


def to_me_with_images(bot: Bot, event: MessageEvent) -> bool:
    plain_text = event.message.extract_plain_text()
    if plain_text.startswith("搜图"):
        return False
    has_image = has_images(event)
    if isinstance(event, PrivateMessageEvent):
        return has_image and config.search_immediately
    # 群里回复机器人发送的消息时，必须带上 "搜图" 才会搜图，否则会被无视
    if event.reply and event.reply.sender.user_id == int(bot.self_id):
        return has_image and "搜图" in plain_text
    at_me = bool(
        [i for i in event.message if i.type == "at" and i.data["qq"] == bot.self_id]
    )
    # 此代码用于尝试解决回复图片搜图和带图片搜图重复发送的问题
    if event.reply:
        return False
    return has_image and (event.to_me or at_me or "搜图" in plain_text)


IMAGE_SEARCH = on_message(rule=Rule(to_me_with_images), priority=5)
IMAGE_SEARCH_MODE = on_command("搜图", priority=5)


@IMAGE_SEARCH_MODE.handle()
async def handle_first_receive(
        event: MessageEvent, matcher: Matcher, args: Message = CommandArg()
) -> None:
    mode, purge, not_r18 = get_args(args)
    matcher.state["ARGS"] = (mode, purge, not_r18)
    if has_images(event):
        matcher.set_arg("IMAGES", args)


# 对图片进行网络搜索
async def image_search(
        url: str,
        md5: str,
        mode: str,
        purge: bool,
        not_r18: bool,
        _cache: Cache,
        client: ClientSession,
        hide_img: bool = config.hide_img,
) -> List[str]:
    url = await get_universal_img_url(url)
    if not purge and (result := exist_in_cache(_cache, md5, mode)):
        if not_r18:
            result = [re.sub(r'\[CQ:image,file=(.+?)\]', '[图片]', res) for res in result]
        return [f"[缓存] {i}" for i in result]
    result = []
    try:
        async for attempt in AsyncRetrying(
                stop=(stop_after_attempt(3) | stop_after_delay(30)), reraise=True
        ):
            with attempt:
                if mode == "a2d":
                    result = await ascii2d_search(url, client, hide_img)
                elif mode == "ex":
                    result = await ehentai_search(url, client, hide_img)
                elif mode == "iqdb":
                    result = await iqdb_search(url, client, hide_img)
                elif mode == "baidu":
                    result = await baidu_search(url, client, hide_img)
                else:
                    result = await saucenao_search(url, mode, client, hide_img)
                    # 仅对涉及到 saucenao 的搜图结果做缓存
                    upsert_cache(_cache, md5, mode, result)


    except Exception as e:
        logger.exception(f"该图 [{url}] 搜图失败")
        result = [f"该图搜图失败\nE: {repr(e)}"]
    # 在r18模式中去处所有缩略图链接
    if not_r18:
        result = [re.sub(r'\[CQ:image,file=(.+?)\]', '[图片]', res) for res in result]
    return result


# 获取QQ消息中的图片链接
async def get_universal_img_url(url: str) -> str:
    final_url = url.replace(
        "/c2cpicdw.qpic.cn/offpic_new/", "/gchat.qpic.cn/gchatpic_new/"
    )
    final_url = re.sub(r"/\d+/+\d+-\d+-", "/0/0-0-", final_url)
    final_url = re.sub(r"\?.*$", "", final_url)
    async with ClientSession(headers=DEFAULT_HEADERS) as session:
        async with session.get(final_url) as resp:
            if resp.status == 200:
                return final_url
    return url


# 获取图片链接和对应的md5值
def get_image_urls_with_md5(event: MessageEvent) -> List[Tuple[str, str]]:
    message = event.reply.message if event.reply else event.message
    return [
        (i.data["url"], str(i.data["file"]).rstrip(".image").upper())
        for i in message
        if i.type == "image" and i.data.get("url")
    ]


# 获取后缀指令
def get_args(msg: Message) -> Tuple[str, bool, bool]:
    mode = "all"
    plain_text = msg.extract_plain_text()
    args = ["pixiv", "danbooru", "doujin", "anime", "a2d", "ex", "iqdb", "baidu"]
    if plain_text:
        for i in args:
            if f"--{i}" in plain_text:
                mode = i
                break
    purge = "--purge" in plain_text
    # 增加一个去处r18图片的指令
    not_r18 = "--r18" in plain_text
    return mode, purge, not_r18


# 转发结果消息
async def send_result_message(
        bot: Bot, event: MessageEvent, msg_list: List[str], index: Optional[int] = None
) -> None:
    # 判断是群聊还是私聊
    if isinstance(event, GroupMessageEvent):
        current_sending_lock = sending_lock[(event.group_id, "group")]
    else:
        current_sending_lock = sending_lock[(event.user_id, "private")]
    if flag := (config.forward_search_result and len(msg_list) > 1):
        try:
            start_time = arrow.now()
            async with current_sending_lock:
                await send_forward_msg(bot, event, msg_list, index)
                await asyncio.sleep(
                    max(1 - (arrow.now() - start_time).total_seconds(), 0)
                )
        except ActionFailed:
            flag = False
    if not flag:
        for msg in msg_list:
            start_time = arrow.now()
            async with current_sending_lock:
                await send_msg(bot, event, msg, index)
                await asyncio.sleep(
                    max(1 - (arrow.now() - start_time).total_seconds(), 0)
                )


async def send_msg(
        bot: Bot, event: MessageEvent, message: str, index: Optional[int] = None
) -> None:
    if index is not None:
        message = f"第 {index + 1} 张图片的搜索结果：\n{message}"
    message = f"{handle_reply_msg(event.message_id)}{message}"
    try:
        await bot.send_msg(
            user_id=event.user_id if isinstance(event, PrivateMessageEvent) else 0,
            group_id=event.group_id if isinstance(event, GroupMessageEvent) else 0,
            message=message,
        )
    except ActionFailed:
        # 去除图片后再次尝试发送
        message = re.sub(r'\[CQ:image,file=(.+?)\]', '[图片]', message)
        await bot.send_msg(
            user_id=event.user_id if isinstance(event, PrivateMessageEvent) else 0,
            group_id=event.group_id if isinstance(event, GroupMessageEvent) else 0,
            message=message,
        )
        # 如果群消息发送失败，则尝试发送私聊消息（仅限好友），私聊消息暂时不可用
        # if isinstance(event, GroupMessageEvent):
        #     friend_list = await get_bot_friend_list(bot)
        #     if event.user_id in friend_list:
        #         with suppress(ActionFailed):
        #             await bot.send_msg(user_id=event.user_id, message=message)


async def send_forward_msg(
        bot: Bot, event: MessageEvent, msg_list: List[str], index: Optional[int] = None
) -> None:
    if index is not None:
        msg_list = [f"第 {index + 1} 张图片的搜索结果："] + msg_list
    msg_list.append(
        "如结果中没有匹配的结果，请尝试将图手动裁切使得图片特征明显后再次搜索（例如在群聊截图中的小图片）。如还是没有，请手动使用Google、Yandex等网站进行尝试。")
    await bot.send_forward_msg(
        user_id=event.user_id if isinstance(event, PrivateMessageEvent) else 0,
        group_id=event.group_id if isinstance(event, GroupMessageEvent) else 0,
        messages=[
            {
                "type": "node",
                "data": {
                    "name": list(config.nickname)[0] if config.nickname else "\u200b",
                    "uin": bot.self_id,
                    "content": msg,
                },
            }
            for msg in msg_list
        ],
    )


@IMAGE_SEARCH.handle()
@IMAGE_SEARCH_MODE.got("IMAGES", prompt="请发送图片")
async def handle_image_search(bot: Bot, event: MessageEvent, matcher: Matcher) -> None:
    # matcher.get_arg()获取消息
    # 输入“退出搜图模式”即可退出
    try:
        if matcher.get_arg("IMAGES").extract_plain_text() == ("退出搜图模式" or "exit"):
            await matcher.finish("已退出搜图模式")
    except AttributeError as e:
        if matcher.get_arg("IMAGES") == ("退出搜图模式" or "exit"):
            await matcher.finish("已退出搜图模式")
    image_urls_with_md5 = get_image_urls_with_md5(event)
    if not image_urls_with_md5:
        await IMAGE_SEARCH_MODE.reject()
    if "ARGS" in matcher.state:
        mode, purge, not_r18 = matcher.state["ARGS"]
    else:
        mode, purge, not_r18 = get_args(event.message)

    # await bot.delete_msg(message_id=int(msg_id))
    # 发送提示消息
    msg_id = await bot.send_msg(
        user_id=event.user_id if isinstance(event, PrivateMessageEvent) else 0,
        group_id=event.group_id if isinstance(event, GroupMessageEvent) else 0,
        message="请稍等，正在搜图...",
    )
    network = (
        Network(proxies=config.proxy, cookies=config.exhentai_cookies, timeout=60)
        if mode == "ex"
        else Network(proxies=config.proxy)
    )
    async with network as client:
        with Cache("picsearch_cache") as _cache:
            for index, (url, md5) in enumerate(image_urls_with_md5):
                await send_result_message(
                    bot,
                    event,
                    await image_search(url, md5, mode, purge, not_r18, _cache, client),
                    index if len(image_urls_with_md5) > 1 else None,
                )
            _cache.expire()
    # 撤回多余消息
    await bot.delete_msg(message_id=int(msg_id["message_id"]))
