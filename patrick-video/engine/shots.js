// Element screenshots of source pages, with the key phrase highlighted like a marked-up document.
const { chromium } = require('playwright');
const HIDE = `figure,.thumb,.infobox,.mw-default-size,table,#siteNotice,.frb,.frb-main,.cdx-dialog-backdrop,#centralNotice,.mw-dismissable-notice,.vector-sticky-header{display:none!important}`;
async function wikiPara(p, url, phrase, file, extraPhrases = []) {
  await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await p.addStyleTag({ content: HIDE });
  await p.waitForTimeout(1500);
  const handle = await p.evaluateHandle(([phrase, extra]) => {
    const paras = [...document.querySelectorAll('#mw-content-text p')];
    const el = paras.find(x => x.textContent.includes(phrase));
    el.querySelectorAll('sup').forEach(s => s.remove());
    for (const ph of [phrase, ...extra]) {
      el.innerHTML = el.innerHTML.replace(ph, `<mark style="background:#ffe14a;padding:0 2px">${ph}</mark>`);
    }
    el.style.cssText += ';padding:18px;background:#fff;max-width:760px;font-size:19px;line-height:1.6';
    return el;
  }, [phrase, extraPhrases]);
  await handle.screenshot({ path: file });
  console.log('ok', file);
}
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1100, height: 1400 }, deviceScaleFactor: 2 });
  await wikiPara(p, 'https://en.wikipedia.org/wiki/Patrick_Star', 'probably the dumbest guy in town', 'doc_dumbest.png', ['"dumb and slow"', '"very active and aggressive"']);
  await wikiPara(p, 'https://en.wikipedia.org/wiki/Patrick_Star', 'was supposed to be a one-time thing', 'doc_lender.png');
  await wikiPara(p, 'https://en.wikipedia.org/wiki/Patrick_Star', 'AquaDauber', 'doc_aquadauber.png');
  await wikiPara(p, 'https://en.wikipedia.org/wiki/Paul_Tibbitt', 'fourth through ninth seasons', 'doc_tibbitt.png');
  await wikiPara(p, 'https://en.wikipedia.org/wiki/The_Patrick_Star_Show', 'July 9, 2021', 'doc_pss.png');
  // Nature article header
  await p.goto('https://www.nature.com/articles/s41586-023-06669-2', { waitUntil: 'domcontentloaded', timeout: 45000 });
  await p.waitForTimeout(2500);
  for (const t of ['Reject optional cookies', 'Accept all cookies']) {
    const btn = p.getByRole('button', { name: t });
    if (await btn.count()) { await btn.first().click(); break; }
  }
  await p.waitForTimeout(800);
  const hdr = p.locator('.c-article-header').first();
  await hdr.evaluate(el => { el.style.background = '#fff'; el.style.padding = '20px'; });
  await hdr.screenshot({ path: 'doc_nature.png' });
  console.log('ok doc_nature.png');
  await b.close();
})();
