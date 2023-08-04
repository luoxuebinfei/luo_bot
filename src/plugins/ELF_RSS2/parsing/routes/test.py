import execjs
import js2py
import subprocess


def get_screen_image():
    node = execjs.get()
    with open('../js/puppeteer-bilibili.js', encoding='utf-8') as f:
        js_code = f.read()
    ctx = node.compile(js_code, cwd=r'..\..\..\..\..\node_modules')
    api_key = ctx.call('run')


def get1():
    path = "../js/puppeteer-bilibili.js"
    param = '825975369859334146'
    save_path = '../cache/bili_dynamic_825975369859334146.png'
    result = subprocess.check_output(['node', path, param, save_path], universal_newlines=True)
    print(result)


if __name__ == '__main__':
    import os

    path1 = os.path.dirname(__file__)
    print(path1)#获取当前运行脚本的绝对路径
    # get1()
