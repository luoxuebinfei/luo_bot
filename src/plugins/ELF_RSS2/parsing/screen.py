import base64
import json
import re
import subprocess

import asyncio
from playwright.async_api import async_playwright, Page
from playwright._impl._api_types import TimeoutError
from nonebot.log import logger
from pathlib import Path
from undetected_playwright import stealth_async


from ..config import config


async def bili_screen(dt_id) -> str | None:
    """
    bilibili的浏览器截图
    :param dt_id:动态ID
    :param save_path:保存路径
    :return: base64
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=200,
                                          args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/115.0.0.0 Safari/537.36",
            locale="zh-cn")
        await stealth_async(context)
        page = await context.new_page()
        # 隐藏webdriver
        js_file_path = Path.cwd() / "tools/stealth.min.js"
        await page.add_init_script(js_file_path.__str__())
        await page.goto(f'https://t.bilibili.com/{dt_id}')
        if config.text_select_captcha:
            await cap(page)
        try:
            await page.locator("//*[@id=\"internationalHeader\"]/div").evaluate_all(
                "nodes=>nodes.forEach((node)=>node.remove())")
            await page.locator('//*[@class="unlogin-popover unlogin-popover-avatar"]').evaluate_all(
                "nodes=>nodes.forEach((node)=>node.remove())")
            await page.mouse.wheel(10000, 10000)
            await page.wait_for_timeout(100)
            await page.locator("//*[@class='login-tip']").evaluate_all("nodes=>nodes.forEach((node)=>node.remove())")
            await page.wait_for_load_state("networkidle", timeout=5000)
        except TimeoutError as e:
            logger.warning(f"哔哩哔哩寻找元素超时：{e}")
        try:
            screenshot_bytes = await page.locator(
                "#app > div.content > div > div > div.bili-dyn-item__main").screenshot(timeout=10000)
            await context.close()
            await browser.close()
            return base64.b64encode(screenshot_bytes).decode()
        except TimeoutError as e:
            logger.warning(f"哔哩哔哩截图超时：{e}")
            await context.close()
            await browser.close()
            return None


async def twitter_screen(dt_id) -> str | None:
    """
    推特的浏览器截图
    :param dt_id:动态ID
    :param save_path:保存路径
    :return: base64
    """
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/115.0.0.0 Safari/537.36",
            locale="zh-cn")
        page = await context.new_page()
        # 隐藏webdriver
        js = "Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});"
        await page.add_init_script(js)
        await page.goto(f'https://twitter.com/fujimatakuya/status/{dt_id}')
        try:
            await page.locator(
                "//*[@id=\"react-root\"]/div/div/div[2]/main/div/div/div/div[1]/div/div[1]/div["
                "1]/div/div/div/div").evaluate("node=>node.style.display='none'")
            await page.locator("//*[@id=\"layers\"]/div").evaluate("node=>node.style.display='none'")
            # 处理可能出现的弹窗
            p = page.locator("xpath=/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div/div[2]")
            if await p.is_visible():
                await p.evaluate("node=>node.style.display='none'")
            await page.wait_for_load_state("networkidle", timeout=5000)
        except TimeoutError as e:
            logger.warning(f"推特寻找元素超时：{e}")
        try:
            screenshot_bytes = await page.get_by_test_id('tweet').screenshot()
            await context.close()
            await browser.close()
            return base64.b64encode(screenshot_bytes).decode()
        except TimeoutError as e:
            logger.warning(f"推特截图失败：{e}")
            await context.close()
            await browser.close()
            return None


async def cap(page: Page):
    """
    解决B站的验证码
    :param page:
    :return:
    """
    n = 0
    while n < 10:
        n += 1
        try:
            if await page.locator(".geetest_item_wrap").is_enabled(timeout=2000):
                logger.info(f"尝试解决B站验证码，第{n}次...")
                a = await page.locator(".geetest_item_wrap").evaluate(
                    '(element) => getComputedStyle(element).getPropertyValue("background-image")')
                url_pattern = r'url\("([^"]+)"\)'
                url = re.findall(url_pattern, a)[0]
                img_ys = page.locator('.geetest_item_img')
                img_box = await img_ys.bounding_box()
                exe_path = Path.cwd() / "tools/Text_select_captcha/Text_select_captcha.exe"
                p = await asyncio.create_subprocess_exec(
                    *[exe_path.__str__(), "-u", url],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                # 等待进程完成或超时
                stdout, stderr = await asyncio.wait_for(p.communicate(), timeout=10)
                for box in json.loads(stdout.decode().strip()):
                    x1, y1, x2, y2 = box
                    x_location = img_box['x'] + x1 + 5
                    y_location = img_box['y'] + y1 + 5
                    await page.mouse.click(x_location, y_location)
                await page.locator(".geetest_commit_tip").click()
                if page.locator(
                        ".geetest_result_tip.geetest_up.geetest_success,.geetest_result_tip.geetest_up.geetest_fail"):
                    if await page.locator(".geetest_success").count() == 1:
                        logger.info("破解验证码成功!")
                        break
                    elif await page.locator(".geetest_fail").count() == 1:
                        # 防止验证码url刷新不及时
                        await page.wait_for_timeout(2500)
                        if await page.locator(".geetest_panel_error_content").is_visible(timeout=2000):
                            await page.locator(".geetest_panel_error_content").click(timeout=2000)
                            continue
                        continue
        except TimeoutError as e:
            logger.warning(e)
            break
        except IndexError:
            continue
        except json.decoder.JSONDecodeError:
            logger.warning("B站验证码识别程序返回错误...")
            continue
        except asyncio.TimeoutError:
            logger.warning("B站验证码识别程序运行错误...")
            continue


if __name__ == '__main__':
    asyncio.run(bili_screen(841806739575668744))
