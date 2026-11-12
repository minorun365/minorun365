#!/usr/bin/env node
// README のカード（表のセル）の余白を、GitHub の本物のスタイルで描画して実測する。
//
//   NODE_PATH=/opt/homebrew/lib/node_modules/@marp-team/marp-cli/node_modules \
//     node assets/check-card-spacing.js [出力PNG]
//
// 公開中のプロフィールページを開き、README の部分だけを手元の README.md の変換結果へ
// 差し替えてから測る。自作のCSSで代用すると見出しの上マージンなどが再現されず、
// 余白が実物と違って見える。
//
// 見るもの（セルの内側の線からの距離。単位 px）:
//   上   … 一番上にある中身（題か挿絵）まで
//   下   … 一番下にある中身（スター数）から
//   左   … 文字の左端まで
//   右   … 挿絵の見える右端から（上と同じ値にする）
//   絵上 … 挿絵の上端と題の文字の上端の差（0 に近いほど頭がそろう）
//   絵間 … 文字と挿絵のいちばん狭い隙間
// セルの左右の余白（14px）と見出しの上マージン（上31px）は GitHub 側の固定値で、README からは変えられない。
// そのため「上と下」をそろえ、角に置く挿絵は上の余白と右の余白をそろえ（右14pxのままだと絵だけ縁に寄って見える）、
// 挿絵の頭を題にそろえ、絵と文字を14px以上離す、を合格条件にする。文字の左14pxは固定値のまま。
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const puppeteer = require('puppeteer-core');

const TOL = 4;
const ROOT = path.resolve(__dirname, '..');
const out = process.argv[2];

function rendered() {
  const md = fs.readFileSync(process.env.README || path.join(ROOT, 'README.md'), 'utf8');
  let html = execFileSync('gh', ['api', 'markdown', '--input', '-'],
    { input: JSON.stringify({ text: md, mode: 'gfm' }), encoding: 'utf8', maxBuffer: 1 << 26 });
  return html.replace(/src="\.\/(assets\/[^"]+)"/g, (_, p) => {
    const mime = p.endsWith('.jpg') ? 'image/jpeg' : 'image/png';
    return `src="data:${mime};base64,${fs.readFileSync(path.join(ROOT, p)).toString('base64')}"`;
  });
}

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new' });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 1000, deviceScaleFactor: 2 });
  await page.goto('https://github.com/minorun365', { waitUntil: 'networkidle2' });
  const rows = await page.evaluate(async (html) => {
    const art = document.querySelector('article.markdown-body');
    art.innerHTML = html;
    await Promise.all([...art.querySelectorAll('img')].map(i => i.decode().catch(() => {})));
    const textRect = (el) => { const r = document.createRange(); r.selectNodeContents(el); return r.getBoundingClientRect(); };
    return [...art.querySelectorAll('td')].filter(td => td.querySelector('h3')).map(td => {
      const c = td.getBoundingClientRect();
      const img = td.querySelector('img[align]');
      const title = textRect(td.querySelector('h3 a'));
      const kids = [...td.querySelectorAll('h3 a, p')].map(textRect).filter(r => r.width);
      const i = img ? img.getBoundingClientRect() : null;
      const top = Math.min(title.top, i ? i.top : 1e9) - c.top;
      const bottom = c.bottom - Math.max(...kids.map(r => r.bottom), i ? i.bottom : 0);
      const left = Math.min(...kids.map(r => r.left)) - c.left;
      const right = i ? c.right - (i.right - 17) : null;   // 台紙の右17pxは透明。見える右端で測る
      const lines = [];
      const w = document.createTreeWalker(td, NodeFilter.SHOW_TEXT);
      for (let n = w.nextNode(); n; n = w.nextNode()) {
        if (!n.textContent.trim()) continue;
        const r = document.createRange(); r.selectNodeContents(n); lines.push(...r.getClientRects());
      }
      // 挿絵の台紙は左に16pxの透明な余白を持つので、見える左端は i.left + 16
      const beside = i ? lines.filter(r => r.bottom > i.top && r.top < i.bottom) : [];
      const gap = beside.length ? Math.min(...beside.map(r => i.left + 16 - r.right)) : null;
      // 段落や題の最後の行が2文字以下で折り返していないか（1文字だけ次の行へ落ちると間が抜けて見える）
      const orphan = [...td.querySelectorAll('h3 a, p')].some(el => {
        const r = document.createRange(); r.selectNodeContents(el);
        const rs = [...r.getClientRects()].filter(x => x.width > 1 && x.height > 14);
        const ys = [...new Set(rs.map(x => Math.round(x.top)))];
        if (ys.length < 2) return false;
        const last = rs.filter(x => Math.round(x.top) === ys[ys.length - 1]);
        return last.reduce((a, x) => a + x.width, 0) < 40;
      });
      return { orphan, name: td.querySelector('h3').textContent.trim().slice(0, 14),
        上: Math.round(top), 下: Math.round(bottom), 左: Math.round(left), 右: right === null ? null : Math.round(right),
        絵上: i ? Math.round(i.top + 4 - (title.top + 4)) : null, row: Math.round(c.top), 絵間: gap === null ? null : Math.round(gap) };
    });
  }, rendered());
  let ng = 0;
  for (const r of rows) {
    // 同じ行のセルは高さがそろうので、文の短いセルは下が余る。行の中で一番詰まったセルが上下そろい、
    // 余りが1行ぶん（24px）以内なら合格にする。
    const rowMin = Math.min(...rows.filter(x => x.row === r.row).map(x => x.下));
    const why = [];
    if (Math.abs(rowMin - r.上) > TOL) why.push('上下');
    if (r.下 - rowMin > 24) why.push('下の余り');
    if (r.右 !== null && Math.abs(r.右 - r.上) > TOL) why.push('絵の角');
    if (Math.abs(r.絵上 ?? 0) > TOL) why.push('絵の頭');
    if (r.絵間 !== null && r.絵間 < 14) why.push('絵と文字');
    if (r.orphan) why.push('行末の孤立');
    if (why.length) ng++;
    console.log(`${why.length ? 'NG' : 'OK'}  上${r.上} 下${r.下} 左${r.左} 右${r.右} 絵上${r.絵上} 絵間${r.絵間}  ${r.name}  ${why.join('・')}`);
  }
  if (out) {
    // 追従する帯（タブの列など）が README の上へ重なったまま写るので、撮る前に流し込みへ戻す。
    // README の枠には内側の余白があるので、要素そのものではなく枠ごと撮る。
    const info = await page.evaluate(() => {
      for (const el of document.querySelectorAll('*')) {
        const p = getComputedStyle(el).position;
        if (p === 'sticky' || p === 'fixed') el.style.position = 'static';
      }
      const art = document.querySelector('article.markdown-body');
      const box = art.closest('.Box, [class*="Box"]') || art.parentElement;
      box.setAttribute('data-shot', '1');
      const a = art.getBoundingClientRect(), b = box.getBoundingClientRect(), img = art.querySelector('img').getBoundingClientRect();
      return { 枠から本文: [Math.round(a.left - b.left), Math.round(a.top - b.top)], バナー: [Math.round(img.left - b.left), Math.round(img.top - b.top), Math.round(b.right - img.right)] };
    });
    console.log(JSON.stringify(info));
    await (await page.$('[data-shot]')).screenshot({ path: out });
  }
  await browser.close();
  console.log(ng ? `NG ${ng}/${rows.length} セル` : `OK ${rows.length} セルの余白がそろっている`);
  process.exit(ng ? 1 : 0);
})();
