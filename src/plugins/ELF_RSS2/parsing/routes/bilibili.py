import asyncio
import os
import re
import subprocess
from typing import Any, Dict

import execjs
from nonebot.log import logger
from pyquery import PyQuery as Pq

from ..handle_images import get_pic_base64
from ...rss_class import Rss
from .. import ParsingBase, handle_html_tag
from ..utils import get_author, get_summary
from ...config import CACHE_PATH


# 处理正文 处理网页 tag
@ParsingBase.append_handler(parsing_type="summary", rex="/bilibili/")
async def handle_summary(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    try:
        tmp += handle_html_tag(html=Pq(get_summary(item)))
    except Exception as e:
        logger.warning(f"{rss.name} 没有正文内容！{e}")

    if author := get_author(item):
        author = f"UP 主： {author}"

    if "AuthorID:" in tmp:
        author_id = re.search(r"\nAuthorID: (\d+)", tmp)[1]  # type: ignore
        tmp = re.sub(r"\nAuthorID: \d+", "", tmp)
        tmp = f"{author}\nUP 主 ID： {author_id}\n{tmp}"
        tmp = (
            tmp.replace("Length:", "时长：")
            .replace("Play:", "播放量：")
            .replace("Favorite:", "收藏量：")
            .replace("Danmaku:", "弹幕数：")
            .replace("Comment:", "评论数：")
            .replace("Match By:", "匹配条件：")
        )
        return tmp

    return f"{author}\n{tmp}"


async def get_screen_image(param, file_name):
    """
    启用无头浏览器puppeteer打开网页进行截图
    :param param: 动态ID
    :param file_name: 保存的文件名
    :return:
    """
    path = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), "js", "bili-puppeteer.js")
    # save_path = os.path.join(os.path.dirname(
    #     os.path.dirname(__file__)), "cache", f"{file_name}")
    save_path = CACHE_PATH / f"{file_name}"  # 规范化路径
    process = await asyncio.create_subprocess_exec("node", path, param, save_path, stdout=asyncio.subprocess.PIPE,
                                                   stderr=asyncio.subprocess.PIPE, )
    _, _ = await process.communicate()
    return


@ParsingBase.append_handler(parsing_type="summary", rex="/bilibili/user/dynamic/")
async def handle_summary(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    """
    将正文文字替换为图片发送
    :param rss:
    :param item: 字典格式的消息
    :param tmp: 正文
    :return: 操作后的正文
    """
    id = re.split(r"/", item["link"])[-1]  # 动态ID
    file_name = f"bili_dynamic_{id}.png"  # 文件名
    # path1 = os.path.dirname(
    #     os.path.dirname(__file__))  # 当前脚本的运行目录"bot.py所在目录\src\plugins\ELF_RSS2\parsing"
    # abs_path = os.path.join(path1, "cache", file_name)  # 保存的图片绝对路径
    abs_path = CACHE_PATH / f"{file_name}"
    if not os.path.exists(abs_path):
        # 如果截图文件不存在，则使用浏览器截图
        _ = await get_screen_image(id, file_name)
    if os.path.exists(abs_path):
        # base64形式上传
        with open(abs_path, 'rb') as f:
            image_data = f.read()
        if img_base64 := get_pic_base64(image_data):
            image_msg = fr"[CQ:image,file=base64://{img_base64},subType=0,url=]"
            os.remove(abs_path)  # 将截图删除
            # 定义正则表达式模式，使用非贪婪匹配来匹配所有可能的翻译之前的所有文字
            pattern = r".*?(?=(谷歌翻译|Deepl翻译|百度翻译))"
            if re.search(pattern,tmp):
                # 使用re.sub()进行正则替换
                tmp = re.sub(pattern, image_msg + "\n", tmp, count=1,flags=re.DOTALL)
            else:
                tmp = image_msg
            return tmp
    else:
        # 如果文件不存在，发送文字消息
        return tmp
