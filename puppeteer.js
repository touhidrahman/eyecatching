const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    const url = process.argv[2];
    const width = parseInt(process.argv[3]);
    const height = parseInt(process.argv[4]);

    await page.goto(url);

    // Get the "viewport" of the page, as reported by the page.
    const dimensions = await page.evaluate(() => {
        return {
            width: document.documentElement.clientWidth,
            height: document.documentElement.clientHeight,
            deviceScaleFactor: window.devicePixelRatio
        };
    });

    await page.setViewport({width: width, height: dimensions.height})


    await page.screenshot({path: 'screenshot.png', fullPage: true});

    await browser.close();
})(); 
