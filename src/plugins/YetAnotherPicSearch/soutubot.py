import asyncio
import json
import os
import re
import sys
import time
import urllib
import http.cookiejar
import io
from typing import List

import execjs
import requests
from aiohttp import ClientSession
from diskcache import Cache
from requests_toolbelt import MultipartEncoder
import webview
import cloudscraper
from pathlib import Path

from . import saucenao_search
from .utils import handle_img
from .config import SOUTUBOT_DATA_PATH
from .cache import upsert_cache

scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance


def read_cookies(window):
    """获取cookie以解决机器人验证"""
    time.sleep(10)
    match = re.search(r"cf_clearance=([^;]+)", str(window.get_cookies()[0]))
    if match:
        # 提取匹配到的内容
        cf_clearance_value = match.group(1)
        cookies["cf_clearance"] = cf_clearance_value
        data["cf_clearance"] = cookies["cf_clearance"]

        window.destroy()  # 关闭窗口


hide_num = 0


def js(window):
    window.hide()
    # global hide_num
    # hide_num += 1
    # if hide_num > 3:
    #     window.show()
    """获取ua"""
    headers["user-agent"] = window.evaluate_js("navigator.userAgent")
    data["user-agent"] = headers["user-agent"]
    read_cookies(window)


def get_api_key():
    node = execjs.get()
    with open(str(Path(__file__).parent / "Soutubot_ApiKey.js"), encoding='utf-8') as f:
        js_code = f.read()
    node_modules_path = Path.cwd() / "node_modules"
    ctx = node.compile(js_code, cwd=rf'{node_modules_path.__str__()}')
    # ctx = node.compile(js_code, cwd=r'D:\Learn\python源码\qq_NoneBot\node_modules')
    api_key = ctx.call('run')
    return api_key


data_path = SOUTUBOT_DATA_PATH / "soutubot.json"

# 检测文件是否存在
if not SOUTUBOT_DATA_PATH.exists():
    SOUTUBOT_DATA_PATH.mkdir(parents=True)
if not data_path.exists():
    with open(data_path.__str__(), "w+", encoding="utf-8") as f:
        f.write(json.dumps({
            "user-agent": "",
            "cf_clearance": ""
        }))

with open(data_path.__str__(), "r", encoding="utf-8") as f:
    try:
        data = json.loads(f.read())
    except json.decoder.JSONDecodeError as e:
        data = {
            "user-agent": "",
            "cf_clearance": ""
        }

headers = {
    "authority": "soutubot.moe",
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "multipart/form-data; boundary=----WebKitFormBoundaryQMMmxCYA7HY7JFLw",
    "dnt": "1",
    "origin": "https://soutubot.moe",
    "referer": "https://soutubot.moe/",
    "sec-ch-ua": r"\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": data["user-agent"],
    "x-api-key": get_api_key(),
    "x-requested-with": "XMLHttpRequest",
}
cookies = {
    "cf_clearance": data["cf_clearance"]
}
soutu_url = "https://soutubot.moe/api/search"

# 重试次数
retry_num = 0


async def soutu_search(url: str, mode: str, client: ClientSession, hide_img: bool, _cache: Cache, md5: str) -> List[
    str]:
    res = requests.get(url)
    f = io.BytesIO(res.content)
    files = {
        'filename': "image",
        'Content-Disposition': 'form-data;',
        'Content-Type': 'form-data',
        'file': ('image', f, 'image/jpeg'),
        'factor': '1.2'
    }
    form_data = MultipartEncoder(files, boundary="----WebKitFormBoundaryQMMmxCYA7HY7JFLw")
    headers["x-api-key"] = get_api_key()
    global retry_num
    if retry_num <= 5:
        response = scraper.post(soutu_url, headers=headers, data=form_data, cookies=cookies)
        retry_num += 1
        # 将 data 写入文件中
        with open(data_path.__str__(), "w", encoding="utf-8") as f:
            f.write(json.dumps(data))
        try:
            json_res = json.loads(response.text)
            final_res = []
            for i in json_res["data"][:3]:
                # 如果匹配度超过80
                thumbnail = await handle_img(i["previewImageUrl"], hide_img)  # 缩略图
                result = [
                    f"SoutuBot（{i['similarity']}%）",
                    f"标题：{i['title']}",
                    thumbnail,
                    f"语言：{i['language']}",
                    f"详情页：{'https://www.' + i['source'] + '.net' + i['subjectPath']}",
                    f"详细页面：{'https://www.' + i['source'] + '.net' + str(i['pagePath'])}" if i[
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
        except json.decoder.JSONDecodeError:
            """遇到机器人验证"""
            window = webview.create_window(title="验证", url="https://soutubot.moe")
            webview.start(js, window, private_mode=False)
            await soutu_search(url, mode, client, hide_img, _cache, md5)
    else:
        return ["soutubot 暂时无法使用"]
