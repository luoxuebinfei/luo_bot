import json

import execjs
import requests
from requests_toolbelt import MultipartEncoder


def get_api_key():
    node = execjs.get()
    with open('Soutubot_ApiKey.js', encoding='utf-8') as f:
        js_code = f.read()
    ctx = node.compile(js_code, cwd=r'..\..\node_modules')
    api_key = ctx.call('run')
    return api_key


def soutu_search(f):
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
        "x-requested-with": "XMLHttpRequest"
    }
    cookies = {
        "cf_clearance": "6d5OSDj94fB4YIXz2icnk.sQDnkEGJQ2pcYfoza7C8c-1685448880-0-250"
    }
    url = "https://soutubot.moe/api/search"

    files = {
        'filename': "image",
        'Content-Disposition': 'form-data;',
        'Content-Type': 'form-data',
        'file': ('image', f, 'image/jpeg'),
        'factor': '1.2'
    }
    form_data = MultipartEncoder(files, boundary="----WebKitFormBoundaryQMMmxCYA7HY7JFLw")
    response = requests.post(url, headers=headers, data=form_data, cookies=cookies)
    try:
        json_res = json.loads(response.text)
        for i in json_res["data"]:
            print("匹配度：", i["similarity"])
            print("标题：", i["title"])
            print("语言：", i["language"])
            print("缩略图：", i["previewImageUrl"])
            print("详情页：", "https://www." + i["source"] + ".net" + i["subjectPath"])
            if i["pagePath"] is not None:
                print("详细页面：", "https://www." + i["source"] + ".net" + str(i["pagePath"]))
            print("\n")
    except json.decoder.JSONDecodeError as e:
        print("触发cloudflare限制")


# print(response.headers)
# print(response)
if __name__ == '__main__':
    # print(get_api_key())
    with open("1.png", "rb") as f:
        soutu_search(f)
