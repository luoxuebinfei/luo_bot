const puppeteer = require('puppeteer');

async function a(param,save_path) {
    console.time("start")
    const browser = await puppeteer.launch(
        {
            headless: true, //设置无头浏览器
            slowMo: 50, //每一步操作延迟
            ignoreDefaultArgs: ["--enable-automation"], //防止网页检测到puppeter
            args: ['--proxy-server=http://127.0.0.1:7890', '--accept-lang=zh'] //设置代理和语言
        }
    );
    const page = await browser.newPage();
    // await page.setUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36")
    await page.goto(`https://twitter.com/azurlane_staff/status/${param}`, {waitUntil: 'networkidle0'});
    // 设置窗口的大小，可以注释下方的一行查看截图的区别
    await page.setViewport({width: 1980, height: 1080});
    // 等待网页完全加载
    await page.reload();
    await page.content();
    // await page.evaluate(()=>{let els = document.evaluate('//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]',document);els.forEach(el => el.remove())})
    await page.evaluate(() => {
        document.evaluate('//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[1]/div/div[1]/div[1]/div/div/div/div', document, null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null).singleNodeValue.style.display = "none";
    }); // 隐藏推文栏
    await page.evaluate(() => {
        document.evaluate('//*[@id="layers"]/div', document, null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null).singleNodeValue.style.display = "none";
    }); // 隐藏未登录底栏
    //获取动态的主体元素
    let dt = await page.$x("//*[contains(@data-testid,'tweet')]");
    await dt[0].screenshot({
        path:  `${save_path}`,

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

