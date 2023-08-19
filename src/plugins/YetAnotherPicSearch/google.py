import asyncio
from typing import Optional, List, Dict, Any

from loguru import logger

from PicImageSearch import Google, Network
from PicImageSearch.model import GoogleResponse
from PicImageSearch.sync import Google as GoogleSync
from nonebot.adapters.onebot.v11 import Bot

from .config import config

#
proxies = config.proxy


# proxies = "http://127.0.0.1:7890"
# url = "https://gchat.qpic.cn/gchatpic_new/1732806519/696540613-2929247948-0EF7B33D23A5913E924547274C9BC5C2/0?term=2&amp;is_origin=1"
# url = "https://gchat.qpic.cn/gchatpic_new/1732806519/696540613-2297316344-87C9ACAFB53CFC7AA398AAABA90FC15B/0?term=2&amp;is_origin=1"


async def google_search(url: str) -> list[str]:
    async with Network(proxies=proxies) as client:
        google = Google(client=client)
        resp = await google.search(url=url)
        result = await show_result(resp)
        if result is None:
            return ["谷歌搜图无结果", f"可尝试使用谷歌智能镜头搜图\nhttps://lens.google.com/uploadbyurl?url={url}"]
        msg_list = ["谷歌搜图结果"] + result + [f"谷歌智能镜头搜图\nhttps://lens.google.com/uploadbyurl?url={url}"]
        return msg_list


async def show_result(resp: Optional[GoogleResponse]) -> list[str] | None:
    if not resp:
        return None
    # logger.info(resp.origin)  # Original Data
    msg_list = [f"搜索结果页面：{resp.url}"]
    # logger.info(resp.url)
    # logger.info(resp.page_number)
    # try to get first result with thumbnail

    for i in (i for i in resp.raw if i.thumbnail):
        prefix = "data:image/jpeg;base64,"
        base64_code = i.thumbnail.split(prefix)[1]
        msg_list.append(f"[CQ:image,file=base64://{base64_code}]\n标题：{i.title}\n详情链接：{i.url}")

    if len(msg_list) == 1:
        return None
    msg_list.append("-" * 50)
    return msg_list


if __name__ == '__main__':
    asyncio.run(test())
