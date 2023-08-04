const puppeteer = require('puppeteer');

async function a(param,save_path) {
    console.time("start")
    const browser = await puppeteer.launch(
        {
            headless: true, //设置无头浏览器
            slowMo: 50, //每一步操作延迟
            ignoreDefaultArgs: ["--enable-automation"] //防止网页检测到puppeter
        }
    );
    const page = await browser.newPage();
    // await page.setUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36")
    await page.goto(`https://t.bilibili.com/${param}`, {waitUntil: 'networkidle0'});
    // 设置窗口的大小，可以注释下方的一行查看截图的区别
    await page.setViewport({width: 1980, height: 1080});
    // 等待网页完全加载
    await page.reload();
    await page.content();
    //删除bilibili的header栏
    await page.evaluate(() => {
        document.evaluate("//*[starts-with(@id,'bili-header')]", document).iterateNext().remove();
    })
    //获取动态的主体元素
    let dt = await page.$("#app > div.content > div > div > div.bili-dyn-item__main")
    const boundingBox = await dt.boundingBox()
    const padding = 10; // 增加的边距
    await dt.screenshot({
        path: `${save_path}`,
    });
    //关闭
    await page.close();
    await browser.close();
    console.timeEnd("start")
}

function run(){
    if (process.argv.length > 2) {
        const param = process.argv[2];
        const save_path = process.argv[3];
        a(param,save_path).then();
    }
}
run()
