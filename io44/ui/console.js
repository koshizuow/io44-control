// io44-control's layout A, "the console": the inputs, the outputs and the reverb as modules with knobs and lit
// buttons, the processing as a row of lamps per mic (a lamp opens that part below), the mixer's faders and meters as a
// console's (style.css, body[data-layout="a"]). Layout B is the page as it was. Both use app.js's state and its ways
// of sending (sendSet, rvSet, the Fat Channel's), so they always agree. The knobs are stream-mic's (its ui/app.js
// knobSvg): dragged up and down (Shift for fine), the wheel, the arrow keys, a double click for the default.

Object.assign(I18N.zh, {
  layout_a: 'A 控台', monitor_blend: '監聽比例', phones: '耳機', main: 'Main', play_side: '播放', in_side: '輸入',
  both_side: '兩邊', mono_main: '單聲道 Main', mono_a: 'A', mono_b: 'B', dry_wet: 'Dry/Wet', rv_lcd_note: '左右箭頭換風格；旋鈕的中間是該風格的建議量',
  lamps_note: '點燈打開那一段的設定', dsp_off_lamps: 'DSP 關', custom_style: '自訂',
});
Object.assign(I18N.en, {
  layout_a: 'A Console', monitor_blend: 'Blend', phones: 'Phones', main: 'Main', play_side: 'playback', in_side: 'inputs',
  both_side: 'both', mono_main: 'Mono Main', mono_a: 'A', mono_b: 'B', dry_wet: 'Dry/Wet', rv_lcd_note: 'The arrows change the style; the knob’s middle is its suggested amount',
  lamps_note: 'A lamp opens that part', dsp_off_lamps: 'DSP off', custom_style: 'Custom',
});

let LAYOUT = 'a';
try { LAYOUT = localStorage.getItem('io44.layout') || 'a'; } catch (e) { /* private window */ }

// ---------------------------------------------------------------- a knob (stream-mic's drawing)
function knobSvg(v, k) {
  const known = v !== undefined && v !== null;
  const a0 = -135, a1 = 135, f = known ? (Math.max(k.min, Math.min(k.max, v)) - k.min) / (k.max - k.min) : 0, ang = a0 + f * (a1 - a0);
  const r = 41, cx = 52, cy = 52;
  const pt = (a, rr) => [(cx + rr * Math.sin(a * Math.PI / 180)).toFixed(2), (cy - rr * Math.cos(a * Math.PI / 180)).toFixed(2)];
  const arc = (from, to) => { const [x0, y0] = pt(from, r), [x1, y1] = pt(to, r); return 'M' + x0 + ' ' + y0 + ' A' + r + ' ' + r + ' 0 ' + (to - from > 180 ? 1 : 0) + ' 1 ' + x1 + ' ' + y1; };
  // bipolar knobs light from the middle
  const from = k.min < 0 && k.max > 0 ? a0 + ((0 - k.min) / (k.max - k.min)) * (a1 - a0) : a0;
  const [lo, hi] = ang < from ? [ang, from] : [from, ang];
  let ticks = '';
  for (let i = 0; i <= 10; i++) {
    const a = a0 + (i / 10) * (a1 - a0), end = i === 0 || i === 10 || i === 5;
    const [x0, y0] = pt(a, 46), [x1, y1] = pt(a, end ? 50.5 : 49);
    ticks += '<line x1="' + x0 + '" y1="' + y0 + '" x2="' + x1 + '" y2="' + y1 + '" stroke="' + (end ? '#5d6570' : '#3a4049') + '" stroke-width="1.2"/>';
  }
  let knurl = '';
  for (let i = 0; i < 40; i++) { const a = (i / 40) * 360, [x0, y0] = pt(a, 26.5), [x1, y1] = pt(a, 30.5); knurl += '<line x1="' + x0 + '" y1="' + y0 + '" x2="' + x1 + '" y2="' + y1 + '"/>'; }
  const [px0, py0] = pt(0, 9), [px1, py1] = pt(0, 22);
  return '<svg viewBox="0 0 104 104" aria-hidden="true"' + (known ? '' : ' class="unknown"') + '>' + ticks +
    '<path d="' + arc(a0, a1) + '" stroke="#20252c" stroke-width="4" fill="none"/>' +
    (known && hi - lo > 0.5 ? '<path d="' + arc(lo, hi) + '" stroke="' + (k.color || 'var(--accent)') + '" stroke-width="4" fill="none"/>' : '') +
    '<circle cx="52" cy="55" r="31" fill="#000" opacity=".55" filter="url(#kShadow)"/><circle cx="52" cy="52" r="31" fill="url(#kSkirt)"/>' +
    '<g transform="rotate(' + ang.toFixed(1) + ' 52 52)"><g stroke="#0b0d10" stroke-width="1.4" opacity=".7">' + knurl + '</g></g>' +
    '<circle cx="52" cy="52" r="31" fill="none" stroke="url(#kRim)" stroke-width="1"/><circle cx="52" cy="52" r="24.5" fill="url(#kCap)"/>' +
    '<circle cx="52" cy="52" r="24.5" fill="none" stroke="url(#kRim)" stroke-width="1"/>' +
    '<ellipse cx="45" cy="42" rx="13" ry="7" fill="url(#kGloss)" transform="rotate(-30 45 42)"/>' +
    '<g transform="rotate(' + ang.toFixed(1) + ' 52 52)"><line x1="' + px0 + '" y1="' + py0 + '" x2="' + px1 + '" y2="' + py1 + '" stroke="#0a0c0e" stroke-width="4" stroke-linecap="round"/>' +
    '<line x1="' + px0 + '" y1="' + py0 + '" x2="' + px1 + '" y2="' + py1 + '" stroke="#f1f3f5" stroke-width="2" stroke-linecap="round"/></g></svg>';
}

// the knobs of the console: their range, how a value reads, what is sent, where the value comes from
const KNOBS = {};
function defKnob(id, k) { KNOBS[id] = Object.assign({ step: 1, size: 92 }, k); }
function knobHtml(id) { const k = KNOBS[id]; return '<div class="knob" data-k="' + id + '" tabindex="0" role="slider" style="--k:' + k.size + 'px"><div class="kd"></div><span class="kn">' + k.name() + '</span><span class="kv num"></span></div>'; }
const kVal = {};   // a knob's value while it is held (the polls do not move it then)
const kShown = {};   // (a typed value draws again: its key changes)   // what each knob shows now: drawn again only when it changes (the meters poll 12 times a second)
function knobShow(id) {
  const el = document.querySelector('.knob[data-k="' + id + '"]'); if (!el) return;
  const k = KNOBS[id], v = kVal[id] !== undefined ? kVal[id] : k.get();
  const key = LANG + ':' + v;
  if (kShown[id] === key && el.querySelector('svg')) return;
  kShown[id] = key;
  el.querySelector('.kd').innerHTML = knobSvg(v, k);
  const kv = el.querySelector('.kv'), known = v !== undefined && v !== null;
  if (kv.dataset.editing === '1') return;
  kv.textContent = known ? k.fmt(v) : t('unknown');
  kv.classList.toggle('unknown', !known);
}
function knobWire(id) {
  const el = document.querySelector('.knob[data-k="' + id + '"]'), k = KNOBS[id];
  const snap = (v) => Math.max(k.min, Math.min(k.max, Math.round(v / k.step) * k.step));
  const set = (v) => { v = snap(v); kVal[id] = v; knobShow(id); k.set(v); };
  const end = () => { if (kVal[id] !== undefined) { const v = kVal[id]; setTimeout(() => { delete kVal[id]; knobShow(id); }, 400); if (k.done) k.done(v); } };
  let drag = null;
  el.addEventListener('pointerdown', (e) => { if (!e.target.closest('svg')) return; el.setPointerCapture(e.pointerId); el.focus(); const v = k.get(); drag = { y: e.clientY, v: v ?? k.min }; kVal[id] = drag.v; });
  el.addEventListener('pointermove', (e) => { if (!drag) return; set(drag.v + (drag.y - e.clientY) * (k.max - k.min) / (e.shiftKey ? 800 : 200)); });
  el.addEventListener('pointerup', () => { if (drag) { drag = null; end(); } });
  el.addEventListener('wheel', (e) => { e.preventDefault(); set((kVal[id] ?? k.get() ?? k.min) - Math.sign(e.deltaY) * k.step * (e.shiftKey ? 1 : 4)); clearTimeout(el._w); el._w = setTimeout(end, 300); }, { passive: false });
  el.addEventListener('keydown', (e) => {
    const d = { ArrowUp: 1, ArrowRight: 1, ArrowDown: -1, ArrowLeft: -1 }[e.key];
    if (d) { e.preventDefault(); set((kVal[id] ?? k.get() ?? k.min) + d * k.step * (e.shiftKey ? 1 : 4)); clearTimeout(el._w); el._w = setTimeout(end, 300); }
  });
  el.addEventListener('dblclick', (e) => { if (k.def !== undefined && e.target.closest('svg')) { set(k.def); end(); } });
  // the value under the knob can be typed (not the blend's two numbers)
  if (id !== 'blend' && typeof numEdit === 'function') numEdit(el.querySelector('.kv'), { lo: k.min, hi: k.max, step: k.step, pan: id.startsWith('p_'),
    get: () => k.get(), apply: (v) => { set(v); end(); } });
}

// ---------------------------------------------------------------- lit buttons
const hbHtml = (id, label, cls) => '<button class="hb ' + (cls || '') + '" id="' + id + '"><i></i>' + label + '</button>';
function hbShow(id, v) {
  const b = $(id); if (!b) return;
  b.classList.toggle('on', v === true);
  b.classList.toggle('unknown', v === undefined);
  b.setAttribute('aria-pressed', String(v === true));
}

// ---------------------------------------------------------------- the processing lamps of a mic
const LAMP = { lowcut: 'LC', gate: 'GT', comp: 'CP', eq: 'EQ', limit: 'LM', voicefx: 'FX' };
function lampsHtml(m) {
  return '<div class="lamps" data-m="' + m + '" title="' + t('lamps_note') + '">' + secsOf(m).map((s) => '<button class="lamp" data-s="' + s + '" title="' + t('f_' + s) + '">' + LAMP[s] + '</button>').join('') + '</div>';
}
function openPart(m, sec) {
  FM = m; SECS = secsOf(m);
  FPICK = sec && SECS.includes(sec) ? sec : SECS.includes(FPICK) ? FPICK : 'lowcut';
  chainBuild(); fatDetailBuild(); fatRender();
  $('fatCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ---------------------------------------------------------------- building and showing the console
const bk = { 0: 'main', 1: 'stream-a', 2: 'stream-b' };
function consoleBuild() {
  for (const b of $('layout').children) { b.textContent = t('layout_' + b.dataset.v); b.onclick = () => setLayout(b.dataset.v); }
  setLayout(LAYOUT, true);
  for (const c of INPUTS) {
    defKnob('g_' + c.key, { name: () => t('gain'), min: c.lo, max: c.hi, step: 0.5, size: 96, fmt: (v) => (+v).toFixed(1) + ' dB',
      get: () => (DEV ? DEV.gain[c.ch] : undefined), set: (v) => sendSet('gain', c.key, v) });
    defKnob('p_' + c.key, { name: () => t('pan'), min: -1, max: 1, step: 0.01, size: 64, def: 0, fmt: fmtPan,
      get: () => setting('pan', c.key), set: (v) => sendSet('pan', c.key, v) });
  }
  defKnob('mainVol', { name: () => t('main'), min: 0, max: 100, step: 1, size: 100, fmt: (v) => Math.round(v) + '%', get: () => (DEV ? DEV.main * 100 : undefined), set: (v) => sendSet('main-volume', '', v) });
  defKnob('blend', { name: () => t('monitor_blend'), min: -1, max: 1, step: 0.02, size: 72, def: 0, fmt: fmtBlend, get: () => setting('blend'), set: (v) => sendSet('blend', '', v) });
  defKnob('phVol', { name: () => t('phones'), min: 0, max: 100, step: 1, size: 72, fmt: (v) => Math.round(v) + '%', get: () => setting('phones-volume'), set: (v) => sendSet('phones-volume', '', v) });
  defKnob('rvAmt', { name: () => t('dry_wet'), min: 0, max: 100, step: 1, size: 84, def: 50, fmt: (v) => (v <= 0 ? t('off') : Math.round(v) + '%'),
    get: () => { const r = setting('reverb'); return r && r.amount !== undefined ? r.amount * 100 : undefined; },
    set: (v) => sendSet('reverb', '', { amount: v / 100 }), done: () => rvSet({}) });

  const tags = { mic1: 'XLR', headset: '3.5 mm', line: '6.3 mm' };
  $('cnsl').innerHTML = INPUTS.map((c) => '<div class="cmod"><div class="mh"><b>' + c.name + '</b><span class="tag">' + tags[c.key] + '</span></div>' +
      '<div class="k2">' + knobHtml('g_' + c.key) + knobHtml('p_' + c.key) + '</div>' +
      (c.ch < 2 ? '<div class="btns">' + hbHtml('c_dsp_' + c.key, t('dsp')) + (c.ch === 0 ? hbHtml('c_p48', t('phantom'), 'red') : '') + hbHtml('c_rec_' + c.key, t('rec')) + '</div>' + lampsHtml(c.key) : '') +
      '</div>').join('') +
    '<div class="cmod"><div class="mh"><b>' + t('outputs') + '</b></div><div class="k3">' + knobHtml('mainVol') + knobHtml('blend') + knobHtml('phVol') + '</div>' +
      '<div class="btns">' + BUSES.map((b) => hbHtml('c_mono_' + b.id, b.id === 0 ? t('mono_main') : t(b.id === 1 ? 'mono_a' : 'mono_b'), 'amber')).join('') + hbHtml('c_phMute', t('phones_mute'), 'amber') + '</div></div>' +
    '<div class="cmod"><div class="mh"><b>Reverb</b></div><div class="lcd"><button id="rvPrev" aria-label="previous">‹</button><div><span id="rvName"></span><small id="rvInfo"></small></div><button id="rvNext" aria-label="next">›</button></div>' +
      '<div class="k2r">' + knobHtml('rvAmt') + '<p class="note">' + t('rv_lcd_note') + '</p></div></div>';
  for (const id in KNOBS) knobWire(id);
  for (const c of INPUTS) {
    if (c.ch > 1) continue;
    $('c_dsp_' + c.key).onclick = () => sendSet('dsp', c.key, !setting('dsp', c.key));
    $('c_rec_' + c.key).onclick = () => sendSet('record_processed', c.key, !setting('record_processed', c.key));
  }
  // 48V: asked first every time it goes on (a ribbon or tube mic can be damaged)
  $('c_p48').onclick = () => { const on = !setting('phantom'); if (!on || confirm(t('phantom_confirm'))) sendSet('phantom', '', on); };
  for (const b of BUSES) $('c_mono_' + b.id).onclick = () => sendSet('mono', bk[b.id], !setting('mono', bk[b.id]));
  $('c_phMute').onclick = () => sendSet('phones-mute', '', !setting('phones-mute'));
  for (const l of document.querySelectorAll('#cnsl .lamps')) l.onclick = (e) => { const b = e.target.closest('.lamp'); if (b) openPart(l.dataset.m, b.dataset.s); };
  const step = (d) => { const r = setting('reverb'), i = Math.max(0, RV_STYLES.indexOf(r && r.style)); rvSet({ style: RV_STYLES[(i + d + RV_STYLES.length) % RV_STYLES.length] }); };
  $('rvPrev').onclick = () => step(-1);
  $('rvNext').onclick = () => step(1);
}

function consoleRender() {
  if (!$('cnsl') || !$('cnsl').children.length) return;
  for (const id in KNOBS) knobShow(id);
  for (const c of INPUTS) {
    if (c.ch > 1) continue;
    hbShow('c_dsp_' + c.key, setting('dsp', c.key));
    hbShow('c_rec_' + c.key, setting('record_processed', c.key));
    // the lamps: each part on or off; all dim with the DSP off (none of it is heard then)
    const f = S.fat ? S.fat[c.key] : null, off = setting('dsp', c.key) === false;
    const l = document.querySelector('#cnsl .lamps[data-m="' + c.key + '"]');
    l.classList.toggle('dspoff', off);
    for (const b of l.children) {
      b.classList.toggle('on', !!f && !!f[b.dataset.s].on);
      b.setAttribute('aria-current', String(FM === c.key && FPICK === b.dataset.s));
    }
  }
  hbShow('c_p48', setting('phantom'));
  for (const b of BUSES) hbShow('c_mono_' + b.id, setting('mono', bk[b.id]));
  hbShow('c_phMute', setting('phones-mute'));
  const r = setting('reverb');
  $('rvName').textContent = !r ? t('unknown') : r.style === 'custom' || !RV_STYLES.includes(r.style) ? t('custom_style') : rvName(r.style);
  const fam = r && rvFamOf(r.style);
  $('rvInfo').textContent = r ? (fam && fam !== 'ours' ? t('fam_' + fam) + ' · ' : '') + Math.round(r.size * 100) + '% · ' + Math.round(r.predelay * 1000) + ' ms · ' + Math.round(r.hp) + ' Hz' : '';
}

function setLayout(v, quiet) {
  LAYOUT = v === 'b' ? 'b' : 'a';
  document.body.dataset.layout = LAYOUT;
  for (const b of $('layout').children) b.setAttribute('aria-pressed', String(b.dataset.v === LAYOUT));
  try { localStorage.setItem('io44.layout', LAYOUT); } catch (e) { /* */ }
  if (!quiet) { drawFatEq(); render(); }
}
