import puppeteer from 'puppeteer';

async function getVideoURL(bvs) {
    const browser = await puppeteer.launch({ headless: true }); // 设置headless:false可以看到浏览器操作
    const pages = await browser.pages(); // 获取当前浏览器中的所有页面
    const currentPage = pages[0]; // 将第一个页面视为当前页面

    var videoUrls = {};

    for (let i = 0; i < bvs.length; i++) {
        try {
            // https://www.bilibili.com/video/{bv}
            await currentPage.goto(`https://www.bilibili.com/video/${bvs[i]}`);
            // 切换设备模式
            await currentPage.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1');
            // 刷新页面
            await currentPage.reload();
            // 等待视频加载完成
            await currentPage.waitForSelector('video');
            // 获取视频地址
            const videoUrl = await currentPage.evaluate(() => {
                return document.querySelector('video').src;
            });
            videoUrls[bvs[i]] = videoUrl;
            console.log(`视频 ${bvs[i]} 的地址为 ${videoUrl}`);
        } catch (error) {
            console.error(`处理视频 ${bvs[i]} 时发生错误: ${error}`);
            videoUrls[bvs[i]] = "获取失败"; // 记录获取失败的情况
        }
    }

    await browser.close();

    // 将视频地址列表转换为 JSON 格式的字符串并返回
    return JSON.stringify(videoUrls);
}

// 获取传递给脚本的命令行参数
const bvList = process.argv.slice(2); // 排除前两个元素，即 Node.js 的执行路径和脚本路径
// 将命令行参数传递给 getVideoURL 函数
getVideoURL(bvList)
    .then(result => {
        console.log(result); // 打印视频地址列表
    })
    .catch(error => {
        console.error(error); // 打印错误信息
    });
