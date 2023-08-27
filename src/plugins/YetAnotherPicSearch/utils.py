import functools
import json
import re
from base64 import b64encode
from contextlib import suppress
from io import BytesIO
from typing import List, Optional, Any

import httpx
from PIL import Image
from aiohttp import ClientSession
from cachetools import TTLCache
from cachetools.keys import hashkey
from nonebot.adapters.onebot.v11 import Bot
from pyquery import PyQuery
from yarl import URL
from nonebot.log import logger

from .config import config

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36"
}


async def get_image_bytes_by_url(
        url: str, cookies: Optional[str] = None
) -> Optional[bytes]:
    headers = {"Cookie": cookies, **DEFAULT_HEADERS} if cookies else DEFAULT_HEADERS
    async with ClientSession(headers=headers) as session:
        async with session.get(url, proxy=config.proxy) as resp:
            if resp.status == 200 and (image_bytes := await resp.read()):
                return image_bytes
    return None


async def content_moderation(url: str, cookies: Optional[str] = None) -> Optional[str]:
    """
    图片审核
    :param url:图片的网址
    :return:
    """
    api = "https://api.moderatecontent.com/moderate/?"
    key = config.review_key
    params = {
        "key": key,
        "url": url
    }
    proxies = {
        "http://": config.proxy,
        "https://": config.proxy,
    }
    headers = {"Cookie": cookies, **DEFAULT_HEADERS} if cookies else DEFAULT_HEADERS
    try:
        async with httpx.AsyncClient(proxies=proxies, headers=headers) as c:
            response = await c.get(api, params=params)
    except httpx.ConnectTimeout as e:
        logger.warning(f"【YetAnotherPicSearch】图片审核服务连接超时")
        return None
    json_res = json.loads(response.text)
    if json_res["error_code"] == 1011:
        logger.warning("【YetAnotherPicSearch】请填入正确的图片审核API")
        return None
    elif json_res["error_code"] == 1001:
        logger.warning(f"【YetAnotherPicSearch】图片审核服务获取图片失败")
        return "Url not accessible or malformed image"
    elif json_res["error_code"] != 0:
        logger.warning(f"【YetAnotherPicSearch】图片审核服务出现错误，错误码：{json_res['error_code']}")
        return None
    return json_res["rating_label"]


async def pixelated_img(bytes_img: Optional[bytes]):
    """
    给图片打码
    :param bytes_img:
    :return:
    """
    img = Image.open(BytesIO(bytes_img))
    # Resize smoothly down to 64x64 pixels
    imgSmall = img.resize((64, 64), resample=Image.Resampling.BILINEAR)

    # Scale back up using NEAREST to original size
    result = imgSmall.resize(img.size, Image.Resampling.NEAREST)
    img_buffer = BytesIO()
    result.save(img_buffer, format='PNG')
    byte_data = img_buffer.getvalue()
    base64_str = b64encode(byte_data).decode()
    return base64_str


async def handle_img(
        url: str,
        hide_img: bool,
        cookies: Optional[str] = None,
) -> str:
    if not hide_img:
        if image_bytes := await get_image_bytes_by_url(url, cookies):
            if len(config.review_key) != 32:
                """当审核api不存在时"""
                if not config.nsfw_img:
                    # nsfw 功能关闭时
                    return f"[CQ:image,file=base64://{b64encode(image_bytes).decode()}]"
                else:
                    # nsfw 功能开启时
                    pixelated_image_bytes = await pixelated_img(image_bytes)
                    return f"[CQ:image,file=base64://{pixelated_image_bytes}]"
            else:
                rating_label = await content_moderation(url, cookies)
                if rating_label == "everyone" or rating_label == "teen" or rating_label == "Url not accessible or malformed image":
                    return f"[CQ:image,file=base64://{b64encode(image_bytes).decode()}]"
                elif rating_label == "adult":
                    pixelated_image_bytes = await pixelated_img(image_bytes)
                    return f"[CQ:image,file=base64://{pixelated_image_bytes}]"
                else:
                    if not config.nsfw_img:
                        # nsfw 功能关闭时
                        return f"[CQ:image,file=base64://{b64encode(image_bytes).decode()}]"
                    else:
                        # nsfw 功能开启时
                        pixelated_image_bytes = await pixelated_img(image_bytes)
                        return f"[CQ:image,file=base64://{pixelated_image_bytes}]"
    return f"预览图链接：{url}"


def cached_async(cache, key=hashkey):  # type: ignore
    """
    https://github.com/tkem/cachetools/commit/3f073633ed4f36f05b57838a3e5655e14d3e3524
    """

    def decorator(func):  # type: ignore
        if cache is None:

            async def wrapper(*args, **kwargs):  # type: ignore
                return await func(*args, **kwargs)

        else:

            async def wrapper(*args, **kwargs):  # type: ignore
                k = key(*args, **kwargs)
                with suppress(KeyError):  # key not found
                    return cache[k]
                v = await func(*args, **kwargs)
                with suppress(ValueError):  # value too large
                    cache[k] = v
                return v

        return functools.update_wrapper(wrapper, func)

    return decorator


@cached_async(TTLCache(maxsize=1, ttl=300))  # type: ignore
async def get_bot_friend_list(bot: Bot) -> List[int]:
    friend_list = await bot.get_friend_list()
    return [i["user_id"] for i in friend_list]


def handle_reply_msg(message_id: int) -> str:
    return f"[CQ:reply,id={message_id}]"


async def get_source(url: str) -> str:
    source = url
    if host := URL(url).host:
        async with ClientSession(headers=DEFAULT_HEADERS) as session:
            if host in ["danbooru.donmai.us", "gelbooru.com"]:
                async with session.get(url, proxy=config.proxy) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        source = PyQuery(html)(".image-container").attr(
                            "data-normalized-source"
                        )
            elif host in ["yande.re", "konachan.com"]:
                async with session.get(url, proxy=config.proxy) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        source = PyQuery(html)("#post_source").attr("value")
                    if not source:
                        source = PyQuery(html)('a[href^="/pool/show/"]').text()

    return source or ""


async def shorten_url(url: str) -> str:
    pid_search = re.compile(
        r"(?:pixiv.+(?:illust_id=|artworks/)|/img-original/img/(?:\d+/){6})(\d+)"
    )
    if pid_search.search(url):
        return f"https://pixiv.net/i/{pid_search.search(url)[1]}"  # type: ignore
    uid_search = re.compile(r"pixiv.+(?:member\.php\?id=|users/)(\d+)")
    if uid_search.search(url):
        return f"https://pixiv.net/u/{uid_search.search(url)[1]}"  # type: ignore
    if URL(url).host == "danbooru.donmai.us":
        return url.replace("/post/show/", "/posts/")
    if URL(url).host in ["exhentai.org", "e-hentai.org", "graph.baidu.com"]:
        flag = len(url) > 1024
        async with ClientSession(headers=DEFAULT_HEADERS) as session:
            if not flag:
                resp = await session.post("https://yww.uy/shorten", json={"url": url})
                if resp.status == 200:
                    return (await resp.json())["url"]  # type: ignore
                else:
                    flag = True
            if flag:
                resp = await session.post(
                    "https://www.shorturl.at/shortener.php", data={"u": url}
                )
                if resp.status == 200:
                    html = await resp.text()
                    final_url = PyQuery(html)("#shortenurl").attr("value")
                    return f"https://{final_url}"
    return url
