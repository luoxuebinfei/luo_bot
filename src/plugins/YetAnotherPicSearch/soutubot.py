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

scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance

# def read_cookies(window):
#     """获取cookie以解决机器人验证"""
#     time.sleep(10)
#     match = re.search(r"cf_clearance=([^;]+)", str(window.get_cookies()[0]))
#     if match:
#         # 提取匹配到的内容
#         cf_clearance_value = match.group(1)
#         cookies["cf_clearance"] = cf_clearance_value
#         data["cf_clearance"] = cookies["cf_clearance"]
#
#         window.destroy()  # 关闭窗口


hide_num = 0


# def js(window):
#     window.hide()
#     # global hide_num
#     # hide_num += 1
#     # if hide_num > 3:
#     #     window.show()
#     """获取ua"""
#     headers["user-agent"] = window.evaluate_js("navigator.userAgent")
#     data["user-agent"] = headers["user-agent"]
#     read_cookies(window)


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
                "cookies": {}
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
                "cookies": {}
            }
        f.close()
    return data


async def write_to_file(data: Coroutine[Any, Any, dict]):
    """
    写入文件
    :param data:
    :return:
    """
    with open(data_path.__str__(), "w+", encoding="utf-8") as f:
        f.write(json.dumps(data))
        f.close()


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
    "user-agent": "",
    "x-api-key": "",
    "x-requested-with": "XMLHttpRequest",
}

soutu_url = "https://soutubot.moe/api/search"


async def soutu_search(url: str, mode: str, client: ClientSession, hide_img: bool, _cache: Cache, md5: str) -> List[
    str]:
    await initialization()
    # 获取图片
    res = requests.get(url)
    img_bytes = res.content
    d = {
        'factor': '1.2',
    }
    file = {
        'file': ('image', img_bytes, 'image/jpeg'),
    }
    retry_num = 0  # 重试次数
    final_res = []
    while retry_num <= 5:
        data: Coroutine[Any, Any, dict] = await read_from_file()
        headers["user-agent"] = data["user-agent"]
        cookies = data["cookies"]
        headers["x-api-key"] = get_api_key()
        try:
            proxies = {
                "http://": config.proxy,
                "https://": config.proxy,
            }
            async with httpx.AsyncClient(proxies=proxies) as c:
                response = await c.post(soutu_url, headers=headers, data=d, files=file, cookies=cookies)
            json_res = json.loads(response.text)
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
        except json.decoder.JSONDecodeError:
            """遇到机器人验证"""
            # window = webview.create_window(title="验证", url="https://soutubot.moe")
            # webview.start(js, window, private_mode=False)
            # 使用 FlareSolverr 解决验证
            logger.info("【SoutuBot】遇到机器人验证，正在使用 FlareSolverr 解决验证...")
            payload = json.dumps(
                {
                    "cmd": "request.get",
                    "url": "https://soutubot.moe/",
                    "maxTimeout": 60000
                }
            )
            headers_ = {
                "Content-Type": "application/json",
                "content-type": "application/json"
            }
            res = requests.post("http://127.0.0.1:8191/v1", data=payload, headers=headers_)
            res = json.loads(res.text)
            ck: list[dict] = res["solution"]["cookies"]
            for i in ck:
                cookies[i["name"]] = i["value"]
            data["user-agent"] = res["solution"]["userAgent"]
            await write_to_file(data)
        except (requests.exceptions.ProxyError, KeyError, httpx.ReadTimeout) as e:
            msg = "【SoutuBot】" + e
            logger.error(msg)
        finally:
            retry_num += 1

    # 如果 soutuBot 无法使用，启用saucenao_search
    sau_result = await saucenao_search(url, mode, client, hide_img)
    final_res = ["soutubot 暂时无法使用\n"]
    final_res.extend(sau_result)
    # 缓存 saucenao 结果
    upsert_cache(_cache, md5, mode, sau_result)
    return final_res
