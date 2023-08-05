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


# 处理图片
@ParsingBase.append_handler(parsing_type="picture", rex="/twitter/")
async def handle_picture(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    # 判断是否开启了只推送标题
    if rss.only_title:
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


async def get_screen_image(param, file_name):
    """
    启用无头浏览器puppeteer打开网页进行截图
    :param param: 动态ID
    :param file_name: 保存的文件名
    :return:
    """
    path = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), "js", "twitter-puppeteer.js")
    # save_path = os.path.join(os.path.dirname(
    #     os.path.dirname(__file__)), "cache", f"{file_name}")
    save_path = CACHE_PATH / f"{file_name}"
    process = await asyncio.create_subprocess_exec("node", path, param, save_path, stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE, )
    _, _ = await process.communicate()
    return


@ParsingBase.append_handler(parsing_type="summary", rex="/twitter/user/", priority=13)
async def handle_summary(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    """
    将正文文字替换为图片发送
    :param rss:
    :param item: 字典格式的消息
    :param tmp: 正文
    :return: 操作后的正文
    """
    id = re.split(r"/", item["link"])[-1]  # 动态ID
    file_name = f"twitter_status_{id}.png"  # 文件名
    # path1 = os.path.dirname(
    #     os.path.dirname(__file__))  # 当前脚本的运行目录"bot.py所在目录\src\plugins\ELF_RSS2\parsing"
    # abs_path = os.path.join(path1, "cache", file_name)  # 保存的图片绝对路径
    abs_path = CACHE_PATH / f"{file_name}"
    if not os.path.exists(abs_path):
        # 如果截图文件不存在，则使用浏览器截图
        _ = await get_screen_image(id, file_name)
    if os.path.exists(abs_path):
        image_msg = fr"[CQ:image,file=file:///{abs_path},subType=0,url=]"
        re_str = item['summary']
        tmp = tmp.replace(re_str, image_msg)
        return tmp
    else:
        # 如果文件不存在，发送文字消息
        return tmp
