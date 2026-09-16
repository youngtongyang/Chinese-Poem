const { chromium } = require('playwright');
const path = require('path');

const URL = 'file://' + path.resolve('/root/code/poem-video/index.html');

(async () => {
  const CHROME = '/root/.agent-browser/browsers/chrome-153.0.8010.47/chrome';
  const browser = await chromium.launch({ args: ['--no-sandbox'], executablePath: CHROME });

  const viewports = [
    { name: 'desktop',  w: 1600, h: 900 },
    { name: 'laptop',   w: 1280, h: 720 },
    { name: 'tablet',   w: 820,  h: 1180 },
    { name: 'iphone',   w: 390,  h: 844 },
    { name: 'iphoneSE', w: 375,  h: 667 },
    { name: 'android',  w: 360,  h: 800 },
  ];

  for (const vp of viewports) {
    const ctx = await browser.newContext({
      viewport: { width: vp.w, height: vp.h },
      deviceScaleFactor: 2,
      isMobile: vp.w <= 900,
      hasTouch: vp.w <= 900,
    });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(String(e)));
    page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });

    await page.goto(URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3200);   // 等入场动画走完

    await page.screenshot({ path: `/root/code/poem-video/vp_${vp.name}.png`, fullPage: vp.w <= 900 });

    // 布局体检
    const diag = await page.evaluate(() => {
      const q = s => document.querySelector(s);
      const r = el => { if (!el) return null; const b = el.getBoundingClientRect();
        return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) }; };
      const overlap = (a, b) => {
        if (!a || !b) return false;
        return !(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y);
      };
      const card = r(q('.author-card')), poem = r(q('.poem')),
            gloss = r(q('.gloss')), title = r(q('.title-block')),
            seal = r(q('.seal')),
            titleMain = r(q('.title-main')),
            toolbar = r(q('.toolbar'));
      // 诗句是否溢出视口
      const cols = [...document.querySelectorAll('.col')].map(r);
      const overflowX = cols.some(c => c && (c.x < -2 || c.x + c.w > innerWidth + 2));
      // 标题是否折行（单行高度 vs 多行）
      const tmEl = q('.title-main');
      const lh = tmEl ? parseFloat(getComputedStyle(tmEl).lineHeight) || tmEl.getBoundingClientRect().height : 0;
      const titleWrapped = tmEl ? tmEl.getBoundingClientRect().height > lh * 1.6 : false;
      const titleOverflowX = tmEl ? tmEl.getBoundingClientRect().right > innerWidth - 4 : false;
      return {
        scrollW: document.documentElement.scrollWidth,
        innerW: innerWidth,
        bodyOverflowX: document.documentElement.scrollWidth > innerWidth + 1,
        card, poem, gloss, title, seal, titleMain, toolbar,
        titleWrapped, titleOverflowX,
        cardOverlapsPoem: overlap(card, poem),
        cardOverlapsGloss: overlap(card, gloss),
        cardOverlapsToolbar: overlap(card, toolbar),
        glossOverlapsCard: overlap(gloss, card),
        titleOverlapsSeal: overlap(titleMain, seal),
        colsOverflowX: overflowX,
        docH: document.documentElement.scrollHeight
      };
    });

    console.log(`\n=== ${vp.name} (${vp.w}x${vp.h}) ===`);
    console.log('errors:', errs.length ? errs : 'none');
    console.log('h-scroll:', diag.bodyOverflowX, `(scrollW ${diag.scrollW} vs ${diag.innerW})`);
    console.log('cols overflow X:', diag.colsOverflowX);
    console.log('title wrapped:', diag.titleWrapped, '| title overflowX:', diag.titleOverflowX);
    console.log('title∩seal:', diag.titleOverlapsSeal, '| card∩toolbar:', diag.cardOverlapsToolbar, '| card∩poem:', diag.cardOverlapsPoem, '| card∩gloss:', diag.cardOverlapsGloss, '| gloss∩card:', diag.glossOverlapsCard);
    console.log('toolbar rect:', JSON.stringify(diag.toolbar), 'card:', JSON.stringify(diag.card), 'documentH:', diag.docH);

    // 短屏专项：滚到底部，确认作者卡没被固定工具列挡住
    if (vp.h <= 700 || vp.w <= 900) {
      const bottomCheck = await page.evaluate(() => {
        window.scrollTo(0, document.documentElement.scrollHeight);
        return new Promise(r => setTimeout(() => {
          const card = document.querySelector('.author-card').getBoundingClientRect();
          const tb = document.querySelector('.toolbar').getBoundingClientRect();
          const ov = !(card.left + card.width <= tb.left || tb.left + tb.width <= card.left ||
                       card.top + card.height <= tb.top || tb.top + tb.height <= card.top);
          r({ overlap: ov, card: {t: Math.round(card.top), b: Math.round(card.bottom)},
              tb: {l: Math.round(tb.left), t: Math.round(tb.top), w: Math.round(tb.width), h: Math.round(tb.height)} });
        }, 400));
      });
      console.log('滚到底部后 card∩toolbar:', bottomCheck.overlap, JSON.stringify(bottomCheck));
    }

    await ctx.close();
  }

  /* ══ 物理引擎测试：验证「春风拂柳」质感 ══ */
  console.log('\n════ 物理引擎测试（桌面 1600x900）════');
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);

  // ① 静置微风：采样 6 秒，看是否持续轻柔飘动（不静止、幅度小）
  const breeze = await page.evaluate(async () => {
    const cols = [...document.querySelectorAll('.poem .col')];
    const samples = [];
    for (let i = 0; i < 60; i++) {
      samples.push(cols.map(c => {
        const m = /translate3d\(([-\d.]+)px, ([-\d.]+)px.*rotate\(([-\d.]+)deg\)/.exec(c.style.transform) || [];
        return { x: +m[1], y: +m[2], r: +m[3] };
      }));
      await new Promise(r => setTimeout(r, 100));
    }
    return samples.map(s => s[0]);   // 取第 1 列
  });
  const xs = breeze.map(s => s.x), rs = breeze.map(s => s.r);
  const ampX = Math.max(...xs) - Math.min(...xs);
  const ampR = Math.max(...rs) - Math.min(...rs);
  const maxAbsX = Math.max(...xs.map(Math.abs));
  // 是否还在动（最后 10 个采样点仍有变化 = 没停死）
  const tail = xs.slice(-10);
  const tailMoving = Math.max(...tail) - Math.min(...tail) > 0.15;
  console.log(`静置微风: 振幅X=${ampX.toFixed(2)}px 振幅Rot=${ampR.toFixed(2)}° 最大|X|=${maxAbsX.toFixed(2)}px 持续飘动=${tailMoving}`);

  // ② 相位检查：4 列是否错开
  const phases = await page.evaluate(() => {
    const cols = [...document.querySelectorAll('.poem .col')];
    return cols.map(c => {
      const m = /translate3d\(([-\d.]+)px/.exec(c.style.transform);
      return +m[1];
    });
  });
  console.log('四列瞬时X（应各不相同→相位错开）:', phases.map(v => v.toFixed(2)).join('  '));

  // ③ 拖拽测试
  const box = await page.locator('.poem .col').nth(1).boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  for (let i = 1; i <= 12; i++) {
    await page.mouse.move(box.x + box.width / 2 - i * 14, box.y + box.height / 2 - i * 5);
    await page.waitForTimeout(16);
  }
  const during = await page.evaluate(() => document.querySelectorAll('.poem .col')[1].style.transform);
  await page.screenshot({ path: '/root/code/poem-video/test_dragging.png' });
  await page.mouse.up();
  await page.waitForTimeout(400);
  const after = await page.evaluate(() => document.querySelectorAll('.poem .col')[1].style.transform);
  await page.waitForTimeout(4000);
  const settled = await page.evaluate(() => document.querySelectorAll('.poem .col')[1].style.transform);
  console.log('拖动中:', during);
  console.log('松手后:', after);
  console.log('4秒后（应回到微风范围，非硬归零）:', settled);

  await ctx.close();
  await browser.close();
})();
