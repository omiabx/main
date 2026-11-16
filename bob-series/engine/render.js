// Frame driver. Usage:
//   node render.js still <scene> <t> <out.jpg> [extraJSON]
//   node render.js video <align.json> <from> <to> <out.mp4> [fps]
//   node render.js info  <align.json>
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const ROOT = __dirname;
const NM = process.env.NODE_MODULES_DIR || path.join(ROOT, 'node_modules');
const types = { '.js': 'text/javascript', '.html': 'text/html', '.woff2': 'font/woff2', '.json': 'application/json' };
function serve() {
  return new Promise((res) => {
    const srv = http.createServer((q, s) => {
      let u = decodeURIComponent(q.url.split('?')[0]); let f;
      if (u.startsWith('/node_modules/')) f = path.join(NM, u.slice(14));
      else if (u.startsWith('/fonts/')) f = path.join(NM, '@fontsource/press-start-2p/files', u.slice(7));
      else f = path.join(ROOT, u === '/' ? 'index.html' : u);
      fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); return s.end(); } s.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); s.end(d); });
    }).listen(0, () => res(srv));
  });
}
(async () => {
  const [mode, ...a] = process.argv.slice(2);
  const srv = await serve(); const port = srv.address().port;
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--disable-gpu-sandbox'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('console', (m) => { if ((m.type() === 'error' || m.type() === 'warning') && !m.text().includes('GPU stall')) console.error('C:', m.text()); });
  p.on('pageerror', (e) => console.log('PAGE ERROR:', e.message));
  await p.goto(`http://localhost:${port}/index.html`); await p.waitForFunction('window.READY', null, { timeout: 60000 });
  const save = (url, f) => fs.writeFileSync(f, Buffer.from(url.split(',')[1], 'base64'));
  if (mode === 'still') {
    await p.evaluate(() => document.fonts.load('40px "PS2P"'));
    const t0 = Date.now(); const url = await p.evaluate(([s, t, x]) => window.API.still(s, t, x), [a[0], +a[1], a[3] ? JSON.parse(a[3]) : null]);
    save(url, a[2]); console.log('still', a[2], Date.now() - t0, 'ms');
  } else if (mode === 'stills') { // stills <align> <out_prefix> t1 t2 ...
    const align = JSON.parse(fs.readFileSync(a[0]));
    await p.evaluate((al) => window.API.init(al), align);
    for (const t of a.slice(2)) { const url = await p.evaluate((t) => window.API.frame(t, 0.9), +t); save(url, `${a[1]}_${(+t).toFixed(1)}.jpg`); }
  } else if (mode === 'info') {
    const align = JSON.parse(fs.readFileSync(a[0]));
    fs.writeFileSync(a[1], JSON.stringify(await p.evaluate((al) => window.API.init(al), align)));
  } else if (mode === 'video') {
    const align = JSON.parse(fs.readFileSync(a[0])); const from = +a[1], to = +a[2], outf = a[3], fps = +(a[4] || 30);
    const info = await p.evaluate((al) => window.API.init(al), align);
    const end = Math.min(to, info.duration);
    const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', outf], { stdio: ['pipe', 'inherit', 'inherit'] });
    const n0 = Math.round(from * fps), n1 = Math.round(end * fps); const tt = Date.now();
    for (let n = n0; n < n1; n++) {
      const url = await p.evaluate((t) => window.API.frame(t, 0.94), n / fps);
      const ok = ff.stdin.write(Buffer.from(url.split(',')[1], 'base64'));
      if (!ok) await new Promise((r) => ff.stdin.once('drain', r));
      if ((n - n0) % 60 === 0) console.log(`${outf} ${n - n0}/${n1 - n0} ${((Date.now() - tt) / Math.max(1, n - n0)).toFixed(0)}ms/f`);
    }
    ff.stdin.end(); await new Promise((r) => ff.on('close', r));
  }
  await b.close(); srv.close();
})();
