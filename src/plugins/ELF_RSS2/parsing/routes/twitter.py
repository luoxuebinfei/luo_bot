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


# async def get_screen_image(param, file_name):
#     """
#     启用无头浏览器puppeteer打开网页进行截图
#     :param param: 动态ID
#     :param file_name: 保存的文件名
#     :return:
#     """
#     path = os.path.join(os.path.dirname(
#         os.path.dirname(__file__)), "js", "twitter-puppeteer.js")
#     # save_path = os.path.join(os.path.dirname(
#     #     os.path.dirname(__file__)), "cache", f"{file_name}")
#     save_path = CACHE_PATH / f"{file_name}"
#     process = await asyncio.create_subprocess_exec("node", path, param, save_path, stdout=asyncio.subprocess.PIPE,
#                                                    stderr=asyncio.subprocess.PIPE, )
#     _, _ = await process.communicate()
#     return

async def get_screen_image(dt_id, save_path):
    """
    获取屏幕截图
    :param dt_id:动态ID
    :param save_path:保存路径
    :return: base64
    """
    await twitter_screen(dt_id, save_path)
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
    dt_id = re.split(r"/", item["link"])[-1]  # 动态ID
    file_name = f"twitter_status_{dt_id}.png"  # 文件名
    save_path = CACHE_PATH / f"{file_name}"
    if not os.path.exists(save_path):
        # 如果截图文件不存在，则使用浏览器截图
        _ = await get_screen_image(dt_id, save_path)
    if os.path.exists(save_path):
        # base64形式上传
        with open(save_path, 'rb') as f:
            image_data = f.read()
        if img_base64 := get_pic_base64(image_data):
            image_msg = fr"[CQ:image,file=base64://{img_base64},subType=0,url=]"
            os.remove(save_path)  # 将截图删除
            # 定义正则表达式模式，使用非贪婪匹配来匹配所有可能的翻译之前的所有文字
            pattern = r".*?(?=(谷歌翻译|Deepl翻译|百度翻译))"
            if re.search(pattern,tmp):
                # 使用re.sub()进行正则替换
                tmp = re.sub(pattern, image_msg + "\n", tmp, count=1,flags=re.DOTALL)
            else:
                tmp = image_msg
            return tmp
        # 文件形式上传
        # image_msg = fr"[CQ:image,file=file:///{save_path},subType=0,url=]"
    else:
        # 如果文件不存在，发送文字消息
        return tmp
