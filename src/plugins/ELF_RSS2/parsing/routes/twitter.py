import asyncio
import os
import re
from typing import Any, Dict

from nonebot.log import logger
from pyquery import PyQuery as Pq
from tenacity import RetryError

from ...rss_class import Rss
from .. import ParsingBase
from ..handle_images import (
    get_preview_gif_from_video,
    handle_img_combo,
    handle_img_combo_with_content,
)
from ..utils import get_summary
from ...config import CACHE_PATH
from ..handle_images import get_pic_base64
from ..screen import twitter_screen


# 处理图片
@ParsingBase.append_handler(parsing_type="picture", rex="/twitter/")
async def handle_picture(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    # 判断是否开启了只推送标题
    if rss.only_title:
        return ""
    if re.match(r"^/twitter/user/", rss.url):
        return ""
    res = await handle_img(
        item=item,
        img_proxy=rss.img_proxy,
        img_num=rss.max_image_number,
    )

    # 判断是否开启了只推送图片
    return f"{res}\n" if rss.only_pic else f"{tmp + res}\n"


# 处理图片、视频
async def handle_img(item: Dict[str, Any], img_proxy: bool, img_num: int) -> str:
    if item.get("image_content"):
        return await handle_img_combo_with_content(
            item.get("gif_url", ""), item["image_content"]
        )
    html = Pq(get_summary(item))
    img_str = ""
    # 处理图片
    doc_img = list(html("img").items())
    # 只发送限定数量的图片，防止刷屏
    if 0 < img_num < len(doc_img):
        img_str += f"\n因启用图片数量限制，目前只有 {img_num} 张图片："
        doc_img = doc_img[:img_num]
    for img in doc_img:
        url = img.attr("src")
        img_str += await handle_img_combo(url, img_proxy)

    # 处理视频
    if doc_video := html("video"):
        img_str += "\n视频预览："
        for video in doc_video.items():
            url = video.attr("src")
            try:
                url = await get_preview_gif_from_video(url)
            except RetryError:
                logger.warning("视频预览获取失败，将发送原视频封面")
                url = video.attr("poster")
            img_str += await handle_img_combo(url, img_proxy)

    return img_str


async def get_screen_image(dt_id):
    """
    获取屏幕截图
    :param dt_id:动态ID
    :return: base64
    """
    return await twitter_screen(dt_id)


@ParsingBase.append_handler(parsing_type="summary", rex="/twitter/user/", priority=13)
async def handle_summary(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    """
    将正文文字替换为图片发送
    :param rss:
    :param item: 字典格式的消息
    :param tmp: 正文
    :return: 操作后的正文
    """
    dt_id = re.split(r"/", item["link"])[-1]  # 动态ID
    if (img_base64 := await get_screen_image(dt_id)) is not None:
        image_msg = fr"[CQ:image,file=base64://{img_base64},subType=0,url=]"
        # 定义正则表达式模式，使用非贪婪匹配来匹配所有可能的翻译之前的所有文字
        pattern = r".*?(?=(谷歌翻译|Deepl翻译|百度翻译))"
        if re.search(pattern, tmp):
            # 使用re.sub()进行正则替换
            tmp = re.sub(pattern, image_msg + "\n", tmp, count=1, flags=re.DOTALL)
        else:
            tmp = image_msg
        return tmp
    else:
        return tmp
