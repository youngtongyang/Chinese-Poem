// 用 Playwright 截图，等待 CSS 动画完成后捕获
const { chromium } = require('/usr/local/lib/hermes-agent/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: '/root/.agent-browser/browsers/chrome-153.0.8010.47/chrome',
    args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars'],
  });
  const targets = [
    { name: 'desktop', w: 1920, h: 1080, url: 'http://127.0.0.1:8899/index.html' },
    { name: 'mobile',  w: 414,  h: 896,  url: 'http://127.0.0.1:8899/index.html' },
  ];
  for (const t of targets) {
    const page = await browser.newPage({ viewport: { width: t.w, height: t.h }, deviceScaleFactor: 2 });
    await page.goto(t.url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(4200);              // 等所有入场动画跑完
    const out = `/root/code/poem-video/shot_${t.name}.png`;
    await page.screenshot({ path: out });
    // 同时抓 DOM 诊断信息
    const diag = await page.evaluate(() => {
      const q = s => document.querySelector(s);
      const r = el => { if (!el) return null; const b = el.getBoundingClientRect();
        return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height),
                 opacity: getComputedStyle(el).opacity, vis: getComputedStyle(el).visibility }; };
      return {
        stage: r(q('.stage')),
        lines: [...document.querySelectorAll('.line')].map(el => ({ text: el.textContent, ...r(el) })),
        title:  r(q('.title-main')),
        author: r(q('.author-line')),
        card:   r(q('.author-card')),
        seal:   r(q('.seal')),
        bodyScroll: { sw: document.body.scrollWidth, sh: document.body.scrollHeight },
      };
    });
    console.log(`\n=== ${t.name} (${t.w}x${t.h}) ===`);
    console.log(JSON.stringify(diag, null, 1));
    await page.close();
  }
  await browser.close();
})();
