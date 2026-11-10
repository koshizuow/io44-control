// Typing a value: every value shown next to a slider, under a knob or a fader, and in the routing matrix can be
// clicked (or focused and Enter) and typed: Enter sends, Esc leaves it, Tab sends and goes to the next one. The
// writing is loose: "-0.5", "+2", "2 dB", "3k", "3.5 kHz", "350", "40 ms", "0.2 s", "50%", and for a pan "C", "L20",
// "R35". A value out of range goes to the nearest end, one between steps to the nearest step; the field flashes
// amber when it was changed so, red when it could not be read (nothing is sent then). What is shown afterwards is what
// the server took. The same as stream-mic's ui/app.js.

function parseNum(text, o = {}) {
  const s = String(text).trim().toLowerCase().replace(/[−－–]/g, '-').replace(/＋/g, '+').replace(/[，。]/g, '.').replace(/\s+/g, ' ');
  if (o.pan) {
    if (/^(c|center|centre|中)$/.test(s)) return 0;
    const p = s.match(/^([lr左右])\s*(\d+(?:\.\d+)?)\s*%?$/);
    if (p) return ((p[1] === 'l' || p[1] === '左') ? -1 : 1) * Math.min(100, +p[2]) / 100;
  }
  const m = s.match(/^([+-]?(?:\d+\.?\d*|\.\d+))\s*(khz|k|hz|db|ms|s|%|:1)?$/);
  if (!m) return NaN;
  let v = +m[1];
  const u = m[2] || '';
  if (u === 'k' || u === 'khz') v *= 1000;
  if (u === 's' && o.unit === 'ms') v *= 1000;
  if (o.pan && Math.abs(v) > 1) v /= 100;   // "-20" for L20
  return v;
}
const isEditing = (el) => !!el && el.dataset.editing === '1';
function plainNum(v, o) {
  if (v === undefined || v === null || !isFinite(v)) return '';
  if (o.pan) return Math.abs(v) < 0.005 ? 'C' : (v < 0 ? 'L' : 'R') + Math.round(Math.abs(v) * 100);
  return String(+(+v).toFixed(3));
}
function snapNum(v, o) {
  if (o.snap) v = o.snap(v);
  else if (o.step) v = Math.round(v / o.step) * o.step;
  v = Math.max(o.lo, Math.min(o.hi, v));
  return +v.toFixed(6);
}
function flash(el, cls) { el.classList.remove('adjusted', 'bad'); void el.offsetWidth; el.classList.add(cls); setTimeout(() => el.classList.remove(cls), 900); }
// el: the element showing the value; o: { lo, hi, step or snap(v), get(): the value now, apply(v), pan, unit }
function numEdit(el, o) {
  if (!el || el.dataset.numed) return;
  el.dataset.numed = '1';
  el.classList.add('numed');
  el.tabIndex = 0;
  const start = () => {
    if (isEditing(el)) return;
    el.dataset.editing = '1';
    const was = el.textContent, inp = document.createElement('input');
    inp.className = 'numin'; inp.value = plainNum(o.get(), o); inp.spellcheck = false;
    el.textContent = ''; el.appendChild(inp); inp.focus(); inp.select();
    let done = false;
    const stop = (text) => { done = true; delete el.dataset.editing; inp.remove(); el.textContent = text; };
    const commit = () => {
      if (done) return true;
      const v = parseNum(inp.value, o);
      if (inp.value.trim() === '' || !isFinite(v)) { stop(was); flash(el, 'bad'); return false; }
      const x = snapNum(v, o);
      stop(was); o.apply(x);
      if (Math.abs(x - v) > 1e-9) flash(el, 'adjusted');
      return true;
    };
    inp.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); commit(); el.focus(); }
      else if (e.key === 'Escape') { e.preventDefault(); stop(was); el.focus(); }
      else if (e.key === 'Tab') {
        e.preventDefault(); commit();
        const all = [...document.querySelectorAll('.numed')].filter((x) => x.offsetParent !== null);
        const next = all[(all.indexOf(el) + (e.shiftKey ? all.length - 1 : 1)) % all.length];
        if (next) next.dispatchEvent(new Event('numedit'));
      }
      e.stopPropagation();
    });
    inp.addEventListener('blur', () => commit());
    inp.addEventListener('pointerdown', (e) => e.stopPropagation());
  };
  el.addEventListener('click', start);
  el.addEventListener('numedit', start);
  el.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !isEditing(el)) { e.preventDefault(); start(); } });
}
// a range input's own min, max and step, its value set as if dragged (its listeners send it)
function rangeEdit(id, extra) {
  const r = $(id);
  numEdit($(id + 'V'), Object.assign({
    lo: +r.min, hi: +r.max, step: +r.step,
    get: () => (r.classList.contains('unknown') ? undefined : +r.value),
    apply: (v) => { r.value = v; r.dispatchEvent(new Event('input')); r.dispatchEvent(new Event('change')); },
  }, extra || {}));
}
