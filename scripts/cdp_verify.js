#!/usr/bin/env node
/**
 * 通用单文件 HTML 回归跑分器（Edge headless + CDP，零依赖 / Node ≥ 21 自带 fetch+WebSocket）
 *
 * 用法:
 *   node cdp_verify.js steps.json
 *
 * steps.json:
 * {
 *   "url": "file:///C:/path/app.html",
 *   "shotDir": "C:/path/shots",
 *   "viewport": { "width": 390, "height": 844, "scale": 2 },
 *   "port": 9400,
 *   "profile": "C:/Users/<user>/AppData/Local/Temp/edgeprof_verify",
 *   "loadWait": 2500,
 *   "steps": [
 *     { "eval": "renderHome()", "wait": 300, "shot": "01-home.png" },
 *     { "expect": "!!document.querySelector('#home h1')" },
 *     { "download": { "expr": "exportReport()", "file": "report.html" } }
 *   ]
 * }
 *
 * 每个 step 可组合 eval / wait / shot / expect / download。
 * 退出码 0 = 全部 expect 通过且页面无报错；1 = 有失败（summary 里能看到哪一条）。
 */
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const EDGE = process.env.EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const cfgPath = process.argv[2];
  if (!cfgPath) { console.error('usage: node cdp_verify.js steps.json'); process.exit(2); }
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  const port = cfg.port || 9400;
  const shotDir = cfg.shotDir || path.join(path.dirname(path.resolve(cfgPath)), 'shots');
  fs.mkdirSync(shotDir, { recursive: true });
  const view = Object.assign({ width: 390, height: 844, scale: 2 }, cfg.viewport || {});
  const profile = cfg.profile || path.join(os.tmpdir(), 'edgeprof_cdp_verify');
  // 每轮清空 profile：localStorage 跨轮保留，会让「本轮应只有 1 条记录」这类断言假失败
  fs.rmSync(profile, { recursive: true, force: true });

  const child = spawn(EDGE, ['--headless=new', '--disable-gpu', '--no-first-run',
    `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, 'about:blank'], { stdio: 'ignore' });
  const bail = msg => { try { child.kill(); } catch (e) {} console.error('FAIL: ' + msg); process.exit(1); };

  let targets = null;
  for (let i = 0; i < 50; i++) {
    await sleep(400);
    try {
      targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      if (targets.some(t => t.type === 'page')) break;
    } catch (e) { /* devtools 还没起来 */ }
  }
  if (!targets || !targets.some(t => t.type === 'page')) bail('devtools 未就绪（检查 Edge 路径 / 端口占用）');

  const page = targets.find(t => t.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let seq = 0; const pending = new Map(); const errors = [];
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    if (m.method === 'Runtime.exceptionThrown')
      errors.push(String(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text).slice(0, 300));
    if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error')
      errors.push('LOG: ' + m.params.entry.text);
  };
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  const send = (method, params = {}) => new Promise(res => {
    const id = ++seq; pending.set(id, res); ws.send(JSON.stringify({ id, method, params }));
  });
  const ev = async expr => {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails)
      return { __err: String(r.result.exceptionDetails.exception?.description).slice(0, 300) };
    return r.result && r.result.result ? r.result.result.value : undefined;
  };

  await send('Runtime.enable');
  await send('Log.enable');
  await send('Page.enable');
  // 手机视口只认这个；--window-size 给的 innerWidth 不是你要的宽度（会被裁图误判成溢出）
  await send('Emulation.setDeviceMetricsOverride',
    { width: view.width, height: view.height, deviceScaleFactor: view.scale, mobile: true });
  await send('Page.navigate', { url: cfg.url });
  await sleep(cfg.loadWait || 2500);

  const results = [];
  let failures = 0;
  const steps = cfg.steps || [];
  for (let i = 0; i < steps.length; i++) {
    const st = steps[i];
    const row = { i };
    if (st.eval) row.value = await ev(st.eval);
    if (st.wait) await sleep(st.wait);
    if (st.shot) {
      const r = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
      fs.writeFileSync(path.join(shotDir, st.shot), Buffer.from(r.result.data, 'base64'));
      row.shot = st.shot;
    }
    if (st.expect) {
      const v = await ev(st.expect);
      row.expect = { expr: st.expect, value: v, ok: !!v };
      if (!v) failures++;
    }
    if (st.download) {
      // 把页面的 download() 换成捕获器，导出的 HTML 落盘，方便人眼 / 打印检查
      const file = path.join(shotDir, st.download.file || ('download-' + i + '.html'));
      const chars = await ev('(() => { window.__cap = null; const old = window.download;' +
        ' window.download = function(t, f){ window.__cap = t };' +
        ' try { ' + st.download.expr + ' } finally { window.download = old; }' +
        ' return window.__cap ? window.__cap.length : 0; })()');
      const text = await ev('window.__cap || ""');
      if (typeof text === 'string' && text) fs.writeFileSync(file, text, 'utf8');
      row.download = { file, chars };
      if (!chars) failures++;
    }
    results.push(row);
  }

  const summary = { ok: failures === 0 && errors.length === 0, failures, errors, results };
  console.log(JSON.stringify(summary, null, 1));
  ws.close();
  child.kill();
  process.exit(summary.ok ? 0 : 1);
})();
