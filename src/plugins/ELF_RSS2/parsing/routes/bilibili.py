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
from ..screen import bili_screen


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


async def get_screen_image(dt_id) -> str | None:
    """
    获取屏幕截图
    :param dt_id:动态ID
    :return: base64
    """
    return await bili_screen(dt_id)


@ParsingBase.append_handler(parsing_type="summary", rex="/bilibili/user/dynamic/")
async def handle_summary(rss: Rss, item: Dict[str, Any], tmp: str) -> str:
    """
    将正文文字替换为图片发送
    :param rss:
    :param item: 字典格式的消息
    :param tmp: 正文
    :return: 操作后的正文
    """
    dt_id = re.split(r"/", item["link"])[-1]  # 动态ID
    # path1 = os.path.dirname(
    #     os.path.dirname(__file__))  # 当前脚本的运行目录"bot.py所在目录\src\plugins\ELF_RSS2\parsing"
    # save_path = os.path.join(path1, "cache", file_name)  # 保存的图片绝对路径
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
