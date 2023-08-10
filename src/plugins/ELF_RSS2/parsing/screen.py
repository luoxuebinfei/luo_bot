import base64

from playwright.async_api import async_playwright
from playwright._impl._api_types import TimeoutError
from nonebot.log import logger


async def bili_screen(dt_id, save_path):
    """
    bilibili的浏览器截图
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
        await page.goto(f'https://t.bilibili.com/{dt_id}')
        await page.mouse.wheel(100, 100)
        p = await page.wait_for_selector("xpath=//*[@id=\"internationalHeader\"]/div")
        await p.evaluate("node=>node.remove()")
        p = await page.wait_for_selector("xpath=//*[@class='login-tip']")
        await p.evaluate("node=>node.remove()")
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except TimeoutError as e:
            logger.warning(e)
        screenshot_bytes = await page.locator("#app > div.content > div > div > div.bili-dyn-item__main").screenshot(
            path=f'{save_path}')
        await context.close()
        await browser.close()
        return base64.b64encode(screenshot_bytes).decode()


async def twitter_screen(dt_id, save_path):
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
        p = await page.wait_for_selector(
            "//*[@id=\"react-root\"]/div/div/div[2]/main/div/div/div/div[1]/div/div[1]/div["
            "1]/div/div/div/div")
        await p.evaluate("node=>node.style.display='none'")
        p = await page.wait_for_selector("//*[@id=\"layers\"]/div")
        await p.evaluate("node=>node.style.display='none'")
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except TimeoutError as e:
            logger.warning(e)
        screenshot_bytes = await page.get_by_test_id('tweet').screenshot(path=f'{save_path}')
        await context.close()
        await browser.close()
        return base64.b64encode(screenshot_bytes).decode()
