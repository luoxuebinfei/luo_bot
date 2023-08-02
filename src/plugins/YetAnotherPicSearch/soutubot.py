import json
import re
import sys
import time
import urllib
import http.cookiejar

import execjs
import requests
from requests_toolbelt import MultipartEncoder
import webview
import cloudscraper

scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance


def read_cookies(window):
    """获取cookie以解决机器人验证"""
    match = re.search(r"cf_clearance=([^;]+)", str(window.get_cookies()[0]))
    if match:
        # 提取匹配到的内容
        cf_clearance_value = match.group(1)
        cookies["cf_clearance"] = cf_clearance_value
        window.destroy()  # 关闭窗口


def js(window):
    """获取ua"""
    headers["user-agent"] = window.evaluate_js("navigator.userAgent")
    read_cookies(window)


def get_api_key():
    node = execjs.get()
    with open('api_key.js', encoding='utf-8') as f:
        js_code = f.read()
    ctx = node.compile(js_code, cwd=r'..\node_modules')
    api_key = ctx.call('run')
    return api_key


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
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 "
                  "Safari/537.36",
    "x-api-key": get_api_key(),
    "x-requested-with": "XMLHttpRequest",
}
cookies = {
    "cf_clearance": ""
}
url = "https://soutubot.moe/api/search"


def img_search():
    with open("1.png", "rb") as f:
        files = {
            'filename': "image",
            'Content-Disposition': 'form-data;',
            'Content-Type': 'form-data',
            'file': ('image', f, 'image/jpeg'),
            'factor': '1.2'
        }
        form_data = MultipartEncoder(files, boundary="----WebKitFormBoundaryQMMmxCYA7HY7JFLw")
        response = scraper.post(url, headers=headers, data=form_data, cookies=cookies)
        try:
            json_res = json.loads(response.text)
            for i in json_res["data"]:
                # print(i)
                print("匹配度：", i["similarity"])
                print("标题：", i["title"])
                print("语言：", i["language"])
                print("缩略图：", i["previewImageUrl"])
                print("详情页：", "https://www." + i["source"] + ".net" + i["subjectPath"])
                if i["pagePath"] is not None:
                    print("详细页面：", "https://www." + i["source"] + ".net" + str(i["pagePath"]))
                print("\n")
        except json.decoder.JSONDecodeError as e:
            """遇到机器人验证"""
            window = webview.create_window(title="验证", url="https://soutubot.moe")
            webview.start(js, window, private_mode=False)
            img_search()


if __name__ == '__main__':
    img_search()
