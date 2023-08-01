import difflib
import json
import time

import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from datetime import datetime
from nonebot.log import logger

ua = UserAgent()
old_push = []  # 老推送
history_push = []  # 历史推送


# 找出两列表中不同的地方
def find_differences(list1, list2):
    differences = [y for y in (list1, list2) if y not in list1]
    return differences


def time_difference(set_timestamp) -> bool:
    """
    判断时间差是否大于5分钟
    :param set_timestamp:设定的时间戳
    :return:布尔值
    """""
    current_timestamp = int(datetime.now().timestamp())
    difference = current_timestamp - set_timestamp
    return difference > 5 * 60  # 5 minutes in seconds


def filter_and_remove_old_dicts():
    """
    过滤掉时间戳不在5分钟之内的字典
    """
    filtered_dicts = []
    global history_push
    for dictionary in history_push:
        timestamp = dictionary.get('shijianchuo')
        if timestamp is None or not time_difference(timestamp):
            filtered_dicts.append(dictionary)
    history_push = filtered_dicts


def calculate_similarity(str1: dict) -> bool:
    """
    判断文本相似度
    :param str1: 一条推送消息的字典
    :return: 布尔值"""
    # 使用difflib.SequenceMatcher计算字符串相似度
    for str2 in history_push:
        matcher = difflib.SequenceMatcher(None, str1["title"], str2["title"])
        similarity = matcher.ratio()
        if similarity >= 0.8:
            return False
    return True


headers = {
    "Referer": "http://new.xianbao.fun/plus/worker.js?v=230406",
    "User-Agent": ua.random,
    "DNT": "1"
}
url = "http://new.xianbao.fun/plus/json/push.json"
params = {
    "230406": ""
}


# 获取简略信息推送
def get_simple_push():
    try:
        headers["User-Agent"] = ua.random
        response = requests.get(url, headers=headers, params=params, verify=False)
        json_res = json.loads(response.text)
        global old_push, history_push
        if len(old_push) == 0:
            old_push, history_push = json_res, json_res
            response = requests.get(url, headers=headers, params=params, verify=False)
            json_res = json.loads(response.text)
        result = []
        # 如果有新推送
        if int(json_res[0]["id"]) > int(old_push[0]["id"]):
            a = [val for val in json_res if val not in old_push]
            if len(a) != 0:
                for i in a:
                    if calculate_similarity(i):
                        msg = f"{i['title']}\n{'http://new.xianbao.fun' + i['url']}"
                        result.append(msg)
                history_push = a + history_push
                old_push = json_res
                filter_and_remove_old_dicts()
        return result
    except json.decoder.JSONDecodeError as e:
        logger.error(e)


# 获取详细信息推送
def get_details_push():
    response = requests.get(url, headers=headers, params=params, verify=False)
    json_res = json.loads(response.text)
    # for i, j in enumerate(json_res):
    #     print(i, j)
    #     print("id:", i["id"])
    #     print("title:", i["title"])
    #     print("url:", "http://new.xianbao.fun/" + i["url"])
    global old_push
    if len(old_push) == 0:
        old_push = json_res
        response = requests.get(url, headers=headers, params=params, verify=False)
        json_res = json.loads(response.text)
    result = []
    # 如果有新推送
    if int(json_res[0]["id"]) > int(old_push[0]["id"]):
        a = [val for val in json_res if val not in old_push]
        if len(a) != 0:
            for i in a:
                b = get_details("http://new.xianbao.fun/" + i["url"])
                result.append(b)
            old_push = json_res
    return result


# 遇到<br/>时在最后结果中也进行换行
def get_text_with_linebreaks_and_images(element):
    result = {'text': '', 'images': []}
    for child in element.children:
        if child.name == 'br':
            result['text'] += '\n'
        elif child.name == 'img' and 'src' in child.attrs:
            result['images'].append(child['src'])
        elif child.string:
            result['text'] += child.string
        elif child.name:
            sub_result = get_text_with_linebreaks_and_images(child)
            result['text'] += sub_result['text']
            result['images'] += sub_result['images']
    return result


# 获取详细信息
def get_details(url):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "max-age=0",
        "DNT": "1",
        "If-Modified-Since": "Wed, 31 May 2023 04:01:39 GMT",
        "If-None-Match": "W/\"6476c6a3-42c8\"",
        "Proxy-Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": ua.random
    }
    cookies = {
        "timezone": "8",
        "mochu_us_notice_alert": "1"
    }
    # url = "http://new.xianbao.fun/weibo/1804011.html"
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    response.encoding = "utf-8"
    try:
        soup = BeautifulSoup(response.text, "lxml")
        a = soup.find("article", {"class": "art-main"})
        # 提取<h1 class="art-title">标签内容
        h1_tag = a.find("h1", class_="art-title")
        h1_content = h1_tag.get_text()
        # print(h1_content)
        # 提取<div class="article-content">标签内容
        div_tag = a.find("div", class_="article-content")
        result_text = get_text_with_linebreaks_and_images(div_tag)
        result_text["title"] = h1_content
        return result_text
    except AttributeError as e:
        return []


if __name__ == '__main__':
    # a = get_details("http://new.xianbao.fun/weibo/1804011.html")
    # print(a)
    # for i in range(5):
    #     a = get_details_push()
    #     time.sleep(15)
    # print(a)
    for i in range(15):
        a = get_simple_push()
        time.sleep(3)
        print(a)
