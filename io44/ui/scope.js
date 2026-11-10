// io44-control's layout B, "the scope": a mic's level over the last 10 seconds with its dynamics drawn over it (the
// thresholds dragged right there), and the mixes as one routing matrix (every source into all three mixes at once).
// The processing card and the sliders' card are the same as before. Uses app.js's state and its ways of sending.
//
// What the io44 reports (2026-11-10, measured through a loopback; device.py GR_MIC1): the level entering Mic 1's
// chain (mic1-chain, what the compressor reads, before the EQ) and the gate's, the compressor's and the limiter's
// gain. It reports no level after the chain, so the processed line is worked out: the chain's input, less the three
// reductions, plus the compressor's makeup (the EQ is not in it). Only levels, about 12 a second: no waveform.

Object.assign(I18N.zh, {
  layout_b: 'B 示波', now: '現在', sc_title: '的電平（最近 10 秒）', sc_in: '進入處理鏈', sc_out: '處理後（估計，不含 EQ）', sc_gr: '壓縮量（Compressor＋Limiter）',
  sc_gate: 'Gate', sc_comp: 'Compressor', sc_lim: 'Limiter 上限', sc_drag: '門檻線可以直接上下拖',
  sc_note: 'io44 只回報電平（每秒約 12 次），不是波形；處理後的線是用處理鏈的入口電平減掉 Gate、Compressor、Limiter 實際壓下的量、加上 makeup 算出來的，不含 EQ。',
  sc_headset: 'Headset 的處理量還沒量過是哪幾個欄位，這裡只畫進入處理鏈的電平。', sc_dspoff: 'DSP 關：處理都不在聲音裡',
  mx_title: '路由矩陣', mx_note: '每個來源送到三個混音各多少。每格左右拖改 dB（按住 Shift 微調），點兩下回到 0 dB，滾輪 ±1 dB，M 是靜音（再按一次回到原來的值）。左邊是來源的電平，最下面是三個混音的輸出電平。',
  mx_src: '來源', mx_out: '輸出',
});
Object.assign(I18N.en, {
  layout_b: 'B Scope', now: 'now', sc_title: ' over the last 10 seconds', sc_in: 'into the chain', sc_out: 'processed (worked out, without the EQ)', sc_gr: 'reduction (compressor + limiter)',
  sc_gate: 'Gate', sc_comp: 'Compressor', sc_lim: 'Limiter ceiling', sc_drag: 'drag a threshold line up and down',
  sc_note: 'The io44 reports levels only (about 12 a second), not the waveform; the processed line is the chain’s input less what the gate, compressor and limiter take, plus the makeup: the EQ is not in it.',
  sc_headset: 'Which of the io44’s readings are the headset’s reductions is not measured yet: only the level into its chain is drawn.', sc_dspoff: 'DSP off: none of the processing is heard',
  mx_title: 'Routing matrix', mx_note: 'How much of each source goes into each mix. Drag a cell left and right (Shift: fine), double click for 0 dB, the wheel for ±1 dB, M mutes (again: back to the value before). On the left each source’s level, at the bottom each mix’s.',
  mx_src: 'Source', mx_out: 'Out',
});

// ---------------------------------------------------------------- the level history
const SC_N = 125;   // 10 s at 80 ms
const HIST = { mic1: [], headset: [] };
function scopePush(m) {
  const g = m['gr-mic1'] || {}, f = S.fat ? S.fat.mic1 : null;
  const lin = (v) => (v === undefined || v === null ? 0 : v);
  const inp = (m['mic1-chain'] || [-150])[0];
  const on = setting('dsp', 'mic1') !== false;
  const gr = { gate: Math.min(0, lin(g.gate)), comp: Math.min(0, lin(g.comp)), limit: Math.min(0, lin(g.limit)) };
  const makeup = on && f && f.comp.on ? +f.comp.makeup : 0;
  const out = on ? inp + gr.gate + gr.comp + makeup + gr.limit : inp;
  HIST.mic1.push({ inp, out, red: -(gr.comp + gr.limit) });
  HIST.headset.push({ inp: (m['mic2-chain?'] || [-150])[0] });
  for (const k in HIST) if (HIST[k].length > SC_N) HIST[k].shift();
  if (document.body.dataset.layout === 'b') drawScope();
}

const SC = { lo: -72, hi: 0 };
let scGeo = null, scDrag = null;
function scLines() {
  const f = F(); if (!f) return [];
  const L = [];
  L.push({ id: 'gate', sec: 'gate', key: 'threshold', v: f.gate.threshold, lo: -80, hi: -20, color: '#6ea8ff', name: t('sc_gate'), on: !!f.gate.on });
  L.push({ id: 'comp', sec: 'comp', key: 'threshold', v: f.comp.threshold, lo: -40, hi: -6, color: '#f2a541', name: t('sc_comp'), on: !!f.comp.on });
  L.push({ id: 'limit', sec: 'limit', key: 'ceiling', v: f.limit.ceiling, lo: -12, hi: 0, color: '#ff5c5c', name: t('sc_lim'), on: !!f.limit.on });
  return L;
}
function drawScope() {
  const c = $('scope'); if (!c) return;
  const [g, w, h] = fitCanvas(c);
  const L = 36, R = w - 8, top = 8, bot = h - 22;
  const y = (d) => top + (bot - top) * (1 - (Math.max(SC.lo, Math.min(SC.hi, d)) - SC.lo) / (SC.hi - SC.lo));
  g.fillStyle = cssv('--inset'); g.fillRect(0, 0, w, h);
  g.font = '10px ' + MONO; g.textAlign = 'left';
  for (let d = 0; d >= SC.lo; d -= 12) { g.fillStyle = 'rgba(255,255,255,.05)'; g.fillRect(L, Math.round(y(d)), R - L, 1); g.fillStyle = cssv('--faint'); g.fillText(String(d), 4, y(d) + 3); }
  g.textAlign = 'center';
  for (let s = 10; s >= 0; s -= 2) { const x = R - (R - L) * s / 10; g.fillStyle = cssv('--faint'); g.fillText(s ? '-' + s + ' s' : t('now'), x, h - 6); }
  const H = HIST[FM] || [], n = H.length, xs = (i) => R - (R - L) * (n - 1 - i) / (SC_N - 1);
  const area = (key, col) => {
    if (!n) return;
    g.beginPath(); g.moveTo(xs(0), bot);
    H.forEach((p, i) => g.lineTo(xs(i), y(p[key])));
    g.lineTo(xs(n - 1), bot); g.closePath(); g.fillStyle = col; g.fill();
  };
  area('inp', 'rgba(160,170,180,.20)');
  if (FM === 'mic1') {
    area('out', 'rgba(79,214,180,.55)');
    // the reduction hangs from the top, 1 dB a 4 px
    if (n) { g.beginPath(); g.moveTo(xs(0), top); H.forEach((p, i) => g.lineTo(xs(i), top + Math.min(60, p.red) * 4)); g.lineTo(xs(n - 1), top); g.closePath(); g.fillStyle = 'rgba(242,165,65,.45)'; g.fill(); }
    const dspOff = setting('dsp', 'mic1') === false;
    for (const l of scLines()) {
      const yy = y(l.v), txt = l.name + ' ' + (+l.v).toFixed(1) + ' dB';
      g.globalAlpha = l.on && !dspOff ? 1 : 0.35;
      g.fillStyle = l.color; g.fillRect(L, Math.round(yy), R - L, 1.5);
      g.font = '600 11px ' + MONO; const tw = g.measureText(txt).width + 14, tx = R - tw - (l.id === 'limit' ? 0 : l.id === 'comp' ? 170 : 340);
      g.fillRect(tx, yy - 9, tw, 18); g.fillStyle = '#0b0d10'; g.textAlign = 'left'; g.fillText(txt, tx + 7, yy + 4);
      g.globalAlpha = 1; l.y = yy;
    }
    if (dspOff) { g.fillStyle = 'rgba(15,17,20,.55)'; g.fillRect(L, top, R - L, bot - top); g.fillStyle = cssv('--warm'); g.font = '600 14px ' + UIF; g.textAlign = 'center'; g.fillText(t('sc_dspoff'), (L + R) / 2, (top + bot) / 2); }
  }
  scGeo = { y, top, bot, L, R };
}
function scopeWire() {
  const c = $('scope');
  const pos = (e) => { const r = c.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
  const toDb = (yy) => SC.lo + (SC.hi - SC.lo) * (1 - (yy - scGeo.top) / (scGeo.bot - scGeo.top));
  const hit = (yy) => FM === 'mic1' && scGeo ? scLines().map((l) => ({ l, d: Math.abs(scGeo.y(l.v) - yy) })).filter((x) => x.d < 7).sort((a, b) => a.d - b.d)[0] : null;
  c.addEventListener('pointerdown', (e) => { const [, yy] = pos(e), h = hit(yy); if (h) { scDrag = h.l; c.setPointerCapture(e.pointerId); } });
  c.addEventListener('pointermove', (e) => {
    const [, yy] = pos(e);
    c.style.cursor = scDrag || hit(yy) ? 'ns-resize' : 'default';
    if (!scDrag) return;
    const v = Math.max(scDrag.lo, Math.min(scDrag.hi, Math.round(toDb(yy) * 2) / 2));
    sendFat(scDrag.sec, scDrag.key, v); drawScope(); fatRender();
  });
  c.addEventListener('pointerup', () => { scDrag = null; });
  new ResizeObserver(() => drawScope()).observe(c);
}

// ---------------------------------------------------------------- the routing matrix
const mxPending = new Map();
function mxValue(b, src) { const m = S.mix[String(b)]; return m && String(src) in m ? m[String(src)] : null; }
function mxSend(b, src, d) {
  const key = b + ':' + src, p = mxPending.get(key);
  (S.mix[String(b)] ||= {})[String(src)] = d;
  if (p) { p.next = d; return; }
  const job = { next: null }; mxPending.set(key, job);
  const go = (v) => api('/api/mix', { bus: b, source: src, db: v }).then(() => { (S.mix[String(b)] ||= {})[String(src)] = v; banner(''); })
    .catch((e) => banner(t('send_fail') + e.message)).finally(() => {
      if (job.next !== null) { const n = job.next; job.next = null; go(n); } else { mxPending.delete(key); render(); }
    });
  go(d);
}
function matrixBuild() {
  $('matrix').innerHTML = '<div class="mxh"><span>' + t('mx_src') + '</span>' + BUSES.map((b) => '<span>' + t(b.key) + '</span>').join('') + '</div>' +
    SOURCES.map((s) => '<div class="mxr" data-s="' + s.id + '"><div class="mxs"><b>' + s.name + '</b><small>' + t(s.kind) + '</small><div class="mxm"><i></i></div></div>' +
      BUSES.map((b) => '<div class="mxc" data-b="' + b.id + '"><div class="mxbar" tabindex="0" role="slider"><b></b></div><span class="num"></span><button class="mxmute">M</button></div>').join('') + '</div>').join('') +
    '<div class="mxr mxo"><div class="mxs"><b>' + t('mx_out') + '</b></div>' + BUSES.map((b) => '<div class="mxc" data-b="' + b.id + '"><div class="mxm big"><i></i></div><span class="num"></span><span></span></div>').join('') + '</div>';
  for (const r of $('matrix').querySelectorAll('.mxr:not(.mxo)')) {
    const src = +r.dataset.s;
    for (const cell of r.querySelectorAll('.mxc')) {
      const b = +cell.dataset.b, bar = cell.querySelector('.mxbar');
      const set = (d) => { d = roundDb(Math.max(-145, Math.min(10, d))); mxSend(b, src, d); mxCell(cell, d); };
      const fromX = (x, fine) => { const rr = bar.getBoundingClientRect(); return Math.max(0, Math.min(1, (x - rr.left) / rr.width)); };
      let drag = null;
      bar.addEventListener('pointerdown', (e) => { bar.setPointerCapture(e.pointerId); bar.focus(); const cur = mxValue(b, src); drag = { x: e.clientX, p: dbToPos(cur ?? 0) }; if (!e.shiftKey) { drag.p = fromX(e.clientX); set(posToDb(drag.p)); } });
      bar.addEventListener('pointermove', (e) => { if (!drag) return; const rr = bar.getBoundingClientRect(); set(posToDb(Math.max(0, Math.min(1, drag.p + (e.clientX - drag.x) * (e.shiftKey ? 0.25 : 1) / rr.width)))); });
      bar.addEventListener('pointerup', () => { drag = null; });
      bar.addEventListener('dblclick', () => set(0));
      numEdit(cell.querySelector('.num'), { lo: -60, hi: 10, step: 0.5, get: () => mxValue(b, src), apply: (d) => set(d) });
      bar.addEventListener('wheel', (e) => { e.preventDefault(); const cur = mxValue(b, src) ?? 0; set((cur <= -100 ? -60 : cur) - Math.sign(e.deltaY) * (e.shiftKey ? 0.5 : 1)); }, { passive: false });
      bar.addEventListener('keydown', (e) => { const d = { ArrowUp: 1, ArrowRight: 1, ArrowDown: -1, ArrowLeft: -1 }[e.key]; if (d) { e.preventDefault(); const cur = mxValue(b, src) ?? 0; set((cur <= -100 ? -60 : cur) + d * (e.shiftKey ? 0.5 : 1)); } });
      // mute: off, and back to the value before (kept in this browser, the same as the console's), 0 dB if none
      cell.querySelector('.mxmute').onclick = () => {
        const cur = mxValue(b, src), key = 'io44.before.' + b + '.' + src;
        if (cur !== null && cur <= -100) { let v = 0; try { v = +(localStorage.getItem(key) ?? 0); } catch (e) { /* */ } set(v); }
        else { try { if (cur !== null) localStorage.setItem(key, cur); } catch (e) { /* */ } set(-145); }
      };
    }
  }
}
function mxCell(cell, d) {
  const known = d !== null, off = known && d <= -100;
  cell.querySelector('.mxbar b').style.width = (known ? dbToPos(d) * 100 : 0) + '%';
  cell.classList.toggle('off', off); cell.classList.toggle('unknown', !known);
  if (cell.querySelector('.num').dataset.editing !== '1') cell.querySelector('.num').textContent = known ? fmtDb(d) : t('unknown');
  cell.querySelector('.mxmute').setAttribute('aria-pressed', String(off));
}
function matrixRender() {
  if (!$('matrix') || !$('matrix').children.length) return;
  for (const r of $('matrix').querySelectorAll('.mxr:not(.mxo)')) for (const cell of r.querySelectorAll('.mxc')) mxCell(cell, mxValue(+cell.dataset.b, +r.dataset.s));
}
function matrixMeters(m) {
  for (const r of $('matrix').querySelectorAll('.mxr:not(.mxo)')) {
    const s = SOURCES.find((x) => x.id === +r.dataset.s), v = Math.max(...(m[s.meter] || [-150]));
    r.querySelector('.mxm i').style.width = pos(v) * 100 + '%';
  }
  for (const cell of $('matrix').querySelectorAll('.mxo .mxc')) {
    const v = Math.max(...(m[BUSES.find((b) => b.id === +cell.dataset.b).meter] || [-150]));
    cell.querySelector('.mxm i').style.width = pos(v) * 100 + '%';
    cell.querySelector('.num').textContent = v < -100 ? '–' : v.toFixed(0) + ' dB';
  }
}

// ---------------------------------------------------------------- building, showing, the meters
function scopeBuild() {
  $('scopeTitle').textContent = '';
  $('scMic').innerHTML = INPUTS.slice(0, 2).map((c) => '<button data-m="' + c.key + '">' + c.name + '</button>').join('');
  $('scMic').onclick = (e) => { const b = e.target.closest('button'); if (b && b.dataset.m !== FM) { FM = b.dataset.m; SECS = secsOf(FM); if (!SECS.includes(FPICK)) FPICK = 'eq'; chainBuild(); fatDetailBuild(); fatRender(); scopeRender(); } };
  $('scLegend').innerHTML = '<span><i style="background:rgba(160,170,180,.5)"></i>' + t('sc_in') + '</span><span><i style="background:var(--accent)"></i>' + t('sc_out') + '</span>' +
    '<span><i style="background:var(--warm)"></i>' + t('sc_gr') + '</span><span class="dim">' + t('sc_drag') + '</span>';
  $('scNote').textContent = t('sc_note');
  $('mxTitle').textContent = t('mx_title');
  $('mxNote').textContent = t('mx_note');
  if (!$('scope').dataset.wired) { scopeWire(); $('scope').dataset.wired = '1'; }
  matrixBuild();
}
function scopeRender() {
  if (!$('scMic')) return;
  for (const b of $('scMic').children) b.setAttribute('aria-pressed', String(b.dataset.m === FM));
  const name = (INPUTS.find((c) => c.key === FM) || {}).name || '';
  $('scopeTitle').textContent = LANG === 'zh' ? name + ' ' + t('sc_title') : name + t('sc_title');
  $('scHeadset').hidden = FM !== 'headset';
  $('scHeadset').textContent = t('sc_headset');
  matrixRender();
  if (document.body.dataset.layout === 'b') drawScope();
}
