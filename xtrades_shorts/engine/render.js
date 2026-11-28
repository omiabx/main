// Usage:
//  node render.js stills <spec.js> <words.json> <outdir> [t1,t2,...|auto]
//  node render.js video  <spec.js> <words.json> <out.mp4> [--fps 30] [--from s --to s]
//  node render.js thumb  <thumbspec.js> <out.png>
const path = require('path'), fs = require('fs'), { spawn } = require('child_process');
const { chromium } = require('playwright');
const [mode, specPath, a2, a3, a4] = process.argv.slice(2);
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
(async () => {
  const spec = require(path.resolve(specPath));
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
  page.on('pageerror', e => { console.error('pageerror:', e.message); process.exitCode = 1; });
  await page.goto('file://' + path.join(__dirname, 'page.html'));
  await page.evaluate(async (logo) => { await XT.init({ logo }); }, 'file://' + path.join(__dirname, '../assets/xtrades-logo.png'));
  const words = mode === 'thumb' ? [{ w: 'x', start: 0, end: 1 }] : JSON.parse(fs.readFileSync(a2));
  const info = await page.evaluate(([s, w]) => XT.compile(s, w), [spec, words]);
  const grab = async (t, frame, fmt) => {
    const d = await page.evaluate(([t, f, fmt]) => { XT.render(t, f); return document.getElementById('c').toDataURL(fmt, 0.95); }, [t, frame, fmt]);
    return Buffer.from(d.split(',')[1], 'base64');
  };
  if (mode === 'thumb') { fs.writeFileSync(a2, await grab(spec.thumbT || 3, 1, 'image/png')); console.log('thumb ->', a2); }
  else if (mode === 'stills') {
    fs.mkdirSync(a3, { recursive: true });
    let times = a4 && a4 !== 'auto' ? a4.split(',').map(Number) : info.scenes.map(s => Math.max(s.t + 0.3, s.end - 0.25));
    const out = [];
    for (let i = 0; i < times.length; i++) { const f = path.join(a3, `scene_${String(i + 1).padStart(2, '0')}.png`); fs.writeFileSync(f, await grab(times[i], i, 'image/png')); out.push({ file: f, t: times[i], scene: info.scenes[i] }); }
    fs.writeFileSync(path.join(a3, 'stills.json'), JSON.stringify(out, null, 1));
    fs.writeFileSync(path.join(a3, 'events.json'), JSON.stringify(await page.evaluate(() => XT.events())));
    console.log(`stills: ${times.length} -> ${a3}  (total ${info.total.toFixed(2)}s)`);
  } else if (mode === 'video') {
    const fps = +arg('--fps', 30), from = +arg('--from', 0), to = +arg('--to', info.total);
    const n = Math.round((to - from) * fps);
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', arg('--preset', 'medium'), '-crf', arg('--crf', '17'), '-pix_fmt', 'yuv420p', '-r', String(fps), a3], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let f = 0; f < n; f++) {
      const buf = await grab(from + f / fps, f, 'image/jpeg');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 300 === 0) console.log(`frame ${f}/${n} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    fs.writeFileSync(a3.replace(/\.mp4$/, '.events.json'), JSON.stringify(await page.evaluate(() => XT.events())));
    console.log(`video: ${n} frames -> ${a3} in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
