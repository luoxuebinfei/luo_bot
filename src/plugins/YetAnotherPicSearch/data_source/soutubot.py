import json
import math
import time
import base64
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import httpx
from nonebot.log import logger
from nonebot_plugin_alconna.uniseg import UniMessage

from ..config import config
from ..cache import msg_cache
from ..registry import (
    SearchFunctionReturnType,
    search_function,
)
from ..utils import (
    async_lock,
    combine_message,
    handle_img,
)

if TYPE_CHECKING:
    from httpx import AsyncClient

# 全局User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def apikey(ua: str):
    """apikey的python实现"""
    timestamp = int(math.pow(round(time.time()), 2) + math.pow(len(ua), 2) + 1562310005776)
    timestamp -= (timestamp % 100)
    b64_str = base64.b64encode(str(timestamp).encode('ascii')).decode('ascii')
    return b64_str.rstrip('=')[::-1]


def calculate_md5(data: bytes) -> str:
    """计算图片MD5哈希值"""
    return hashlib.md5(data).hexdigest()


async def get_result_by_api(image_bytes: bytes) -> Optional[dict]:
    """使用api请求"""
    try:
        data = {
            'factor': '1.2',
        }
        files = {
            'file': ('image', image_bytes, 'application/octet-stream'),
        }
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "x-api-key": apikey(USER_AGENT),
            "x-requested-with": "XMLHttpRequest",
            "sec-ch-ua-platform": "\"Windows\"",
            "origin": "https://soutubot.moe",
            "referer": "https://soutubot.moe/",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-language": "zh-CN,zh;q=0.9",
        }
        proxies = {
            "http://": config.proxy,
            "https://": config.proxy,
        } if config.proxy else None
        async with httpx.AsyncClient(proxies=proxies) as client:
            response = await client.post(
                "https://soutubot.moe/api/search",
                headers=headers,
                data=data,
                files=files,
                timeout=20
            )
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"soutubot_api响应状态码：{response.status_code}\n响应内容：{response.text}")

    except httpx.ReadTimeout:
        logger.warning("soutubot连接读取超时...")
    except Exception as e:
        logger.error(f"soutubot请求出错：{e}")

    return None


def get_full_url(source: str, path: str) -> str:
    """根据来源和路径获取完整URL"""
    base_urls = {
        "nhentai": "https://nhentai.net",
        "ehentai": "https://e-hentai.org",
        "pixiv": "https://www.pixiv.net",
    }
    return f"{base_urls.get(source, '')}{path}"


def get_language_text(language_code: str) -> str:
    """获取语言显示文本"""
    language_map = {
        "jp": "日文",
        "cn": "中文",
        "gb": "英文",
        "kr": "韩文",
    }
    return language_map.get(language_code, language_code)


async def process_search_results(result: dict) -> List[UniMessage]:
    """处理搜索结果"""
    final_res: List[UniMessage] = []

    # 使用全局hide_img或特定的hide_soutubot_img配置
    hide_img = config.hide_img or config.hide_soutubot_img

    # 取前3个结果
    for index, item in enumerate(result["data"][:3]):
        source = item.get("source", "未知来源")
        similarity = item.get("similarity", 0)
        title = item.get("title", "无标题")
        language = get_language_text(item.get("language", ""))
        subject_path = item.get("subjectPath", "")
        page_path = item.get("pagePath", "")
        url = get_full_url(source, subject_path)
        preview_url = item.get("previewImageUrl", "")

        thumbnail = await handle_img(preview_url, hide_img) if not hide_img else UniMessage.text("")

        res_list = [
            f"Soutubot ({source}, {similarity:.2f}%)",
            thumbnail,
            title,
            f"语言：{language}" if language else "",
            f"详情页：{url}",
            f"图片页：{get_full_url(source, page_path)}" if page_path else ""
        ]

        final_res.append(combine_message(res_list))

    # 添加搜索信息
    if "executionTime" in result and "imageUrl" in result:
        search_info = [
            f"执行时间：{result.get('executionTime', 0):.2f}秒",
        ]
        final_res.append(UniMessage.text("\n").join([
            UniMessage.text(""),
            combine_message(search_info)
        ]))

    return final_res


@search_function("soutubot")
@async_lock(freq=8)
async def soutubot_search(
    file: bytes,
    client: "AsyncClient",
    mode: str,
    purge: bool = False,
) -> SearchFunctionReturnType:
    """Soutubot搜索引擎"""
    # 计算图片MD5，用于缓存
    md5 = calculate_md5(file)
    cache_key = f"soutubot_{md5}"

    # 检查缓存
    if not purge and (cached_msgs := msg_cache.get(cache_key)):
        logger.info(f"使用缓存结果: {cache_key}")
        return cached_msgs, None

    # 进行搜索
    result = await get_result_by_api(file)

    if not result or "data" not in result or not result["data"]:
        return [UniMessage.text("Soutubot 未找到相关结果或暂时无法使用")]

    # 处理搜索结果
    final_res = await process_search_results(result)

    # 存入缓存
    if final_res:
        msg_cache[cache_key] = final_res

    return final_res, None