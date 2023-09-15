import json

import httpx
from nonebot.log import logger
from typing import List, Any, Coroutine

import execjs
import requests
from aiohttp import ClientSession
from diskcache import Cache

import cloudscraper
from pathlib import Path

from .config import config
from . import saucenao_search
from .utils import handle_img
from .config import SOUTUBOT_DATA_PATH
from .cache import upsert_cache
from playwright.async_api import async_playwright
from undetected_playwright import stealth_async

data_path = SOUTUBOT_DATA_PATH / "soutubot.json"


async def initialization():
    """
    初始化文件，检查文件是否存在，不存在则创建
    :return:
    """
    # 检测文件是否存在
    if not SOUTUBOT_DATA_PATH.exists():
        SOUTUBOT_DATA_PATH.mkdir(parents=True)
    if not data_path.exists():
        with open(data_path.__str__(), "w+", encoding="utf-8") as f:
            f.write(json.dumps({
                "user-agent": "",
                "cookies": []
            }))
            f.close()


async def read_from_file():
    """
    从文件中读取ua和cookies
    :return:
    """
    with open(data_path.__str__(), "r", encoding="utf-8") as f:
        try:
            data = json.loads(f.read())
        except json.decoder.JSONDecodeError as e:
            data = {
                "user-agent": "",
                "cookies": []
            }
        f.close()
    return data


async def write_to_file(data: dict):
    """
    写入文件
    :param data:
    :return:
    """
    with open(data_path.__str__(), "w+", encoding="utf-8") as f:
        f.write(json.dumps(data))
        f.close()


async def cf() -> (str, str):
    """
    解决cloudflare验证
    :return:
    """
    url = "http://127.0.0.1:8191/v1"
    payload = {
        "cmd": "request.get",
        "url": "https://soutubot.moe/",
        "maxTimeout": 60000,
        "proxy": {"url": "http://127.0.0.1:7890"}
    }
    headers = {
        "Content-Type": "application/json",
        "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        cookies, useragent = response.json()["solution"]["cookies"], response.json()["solution"]["userAgent"]
        await write_to_file({"cookies": cookies, "user-agent": useragent})
        return cookies, useragent
    else:
        logger.error(f"【Soutubot】FlareSolverr 出现错误")
        return None, None


async def get_result(image_bytes: bytes, cookies: str = None, useragent: str = None) -> dict | None:
    """
    获取搜图结果
    :param useragent:
    :param cookies:
    :param image_bytes: 传入的图片字节
    :return: json结果或者None
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        if cookies is None:
            cookies, useragent = await cf()
            # 如果 FlareSolverr 出现错误，则退出
            if cookies is None:
                await browser.close()
                return None
        context = await browser.new_context(user_agent=useragent, locale="zh-cn")
        await context.add_cookies(cookies)
        await stealth_async(context)
        page = await context.new_page()
        # 隐藏webdriver
        js_file_path = Path.cwd() / "tools/stealth.min.js"
        await page.add_init_script(js_file_path.__str__())
        await page.goto("https://soutubot.moe/")
        # 检查cookies是否过期
        if await page.get_by_text("检查站点连接是否安全").is_visible():
            await context.close()
            await browser.close()
            return await get_result(image_bytes, None, None)
        # await page.screenshot(path=Path.cwd() / "src/plugins/YetAnotherPicSearch/1.png".__str__())
        # 获取响应对象
        async with page.expect_response("https://soutubot.moe/api/search") as response_info:
            # with open(r'D:\Learn\python源码\SpiderLearn\Soutubot\1.png', 'rb') as f:
            #     await page.set_input_files('//*[@id="app"]/div/div/div/div[1]/div[2]/div/input', files=[
            #         {"name": "1.png", "mimeType": "image/png", "buffer": f.read()}
            #     ], )
            await page.set_input_files('//*[@id="app"]/div/div/div/div[1]/div[2]/div/input', files=[
                {"name": "1.png", "mimeType": "image/png", "buffer": image_bytes}
            ])
        response = await response_info.value
        result: dict = await response.json()
        await context.close()
        await browser.close()
        if response.status == 200:
            return result
        else:
            return None


async def soutu_search(url: str, mode: str, client: ClientSession, hide_img: bool, _cache: Cache, md5: str) -> List[
    str]:
    await initialization()
    # 获取图片
    res = requests.get(url)
    img_bytes = res.content
    final_res = []
    # 不启用 SoutuBot 时直接返回 sau 搜索结果
    if not config.soutubot_open:
        sau_result = await saucenao_search(url, mode, client, hide_img)
        final_res.extend(sau_result)
        return final_res
    try:
        # 从文件中读取
        data = await read_from_file()
        cookies, useragent = data["cookies"], data["user-agent"]
        json_res = await get_result(img_bytes, cookies, useragent)
        for i in json_res["data"][:3]:
            # 如果匹配度超过80
            thumbnail = await handle_img(i["previewImageUrl"], hide_img)  # 缩略图
            if i['source'] == "nhentai":
                result = [
                    f"SoutuBot（{i['similarity']}%）",
                    f"标题：{i['title']}",
                    thumbnail,
                    f"语言：{i['language']}",
                    f"详情页：{'https://www.' + i['source'] + '.net' + i['subjectPath']}",
                    f"详细页面：{'https://www.' + i['source'] + '.net' + str(i['pagePath'])}" if i[
                                                                                                    "pagePath"] is not None else "",
                ]
            else:
                result = [
                    f"SoutuBot（{i['similarity']}%）",
                    f"标题：{i['title']}",
                    thumbnail,
                    f"语言：{i['language']}",
                    f"详情页：{'https://' + 'e-hentai.org' + i['subjectPath']}\n{'https://' + 'exhentai.org' + i['subjectPath']}",
                    f"详细页面：{'https://' + 'e-hentai.org' + str(i['pagePath'])}\n{'https://' + 'exhentai.org' + str(i['pagePath'])}" if
                    i[
                        "pagePath"] is not None else "",
                ]
            if i["similarity"] >= 60:
                res_list = result
                final_res.append("\n".join([i for i in res_list if i]))
                break
            elif 40 <= i["similarity"] < 60:
                res_list = result
                final_res.append("\n".join([i for i in res_list if i]))
            else:
                res_list = result
                final_res.append("\n".join([i for i in res_list if i]))
                sau_result = await saucenao_search(url, mode, client, hide_img)
                # 如果相似度过低，启用saucenao_search
                final_res.extend(sau_result)
                # 缓存 saucenao 结果
                upsert_cache(_cache, md5, mode, sau_result)
                break
        return final_res
    except TypeError as e:
        logger.error(f"【SoutuBot】发生错误：{e}")

    # 如果 soutuBot 无法使用，启用saucenao_search
    sau_result = await saucenao_search(url, mode, client, hide_img)
    final_res = ["soutubot 暂时无法使用\n"]
    final_res.extend(sau_result)
    return final_res
