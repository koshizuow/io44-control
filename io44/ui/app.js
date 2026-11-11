// io44-control's page: the three mixes of a Revelator io44 as faders, its meters, the PipeWire names.
// The io44 does not report its mixes: this computer keeps all the settings (state.json, by the server) and writes
// them whenever the io44 is there.
'use strict';

const I18N = {
  zh: {
    connected: '已連線', offline: '沒有連上 io44', main_knob: 'Main 旋鈕', unknown: '未知', off: '關',
    mute: '靜音', muted: '已靜音', bus_main: 'Main', bus_a: 'Stream Mix A', bus_b: 'Stream Mix B',
    note_main: '喇叭和耳機聽到的混音。', note_a: '錄音的第 5–6 聲道（直播、Discord 用）。', note_b: '錄音的第 7–8 聲道（第二組直播混音）。',
    unknown_note: 'io44 不回報混音的設定，所以由這台電腦保存全部設定，io44 每次接上都整份寫入。第一次使用時從中性的預設值開始（所有輸入以 0 dB 進各混音，增益和監聽比例照 io44 現在的值）。拖曳推桿、滾輪或方向鍵調整（按住 Shift 微調），雙擊回到 0 dB。',
    k_input: '輸入', k_playback: '電腦播放', k_fx: '效果器', bus_out: '輸出',
    pw_title: 'PipeWire 裝置名稱', pw_on: '已安裝', pw_offstate: '未安裝',
    pw_note: 'Linux 預設把 io44 當成「環繞 2.1 輸出／7.1 輸入」：8 個輸入聲道混成一個裝置，Virtual A/B 送不到。安裝後會拆成下面這些有名字的裝置。安裝和移除都會重新啟動 PipeWire，聲音會中斷一下。',
    pw_install: '安裝', pw_remove: '移除', pw_working: '處理中…',
    pw_confirm_install: '要重新啟動 PipeWire，並把預設輸出換成「io44 Playback」嗎？',
    pw_confirm_remove: '要移除設定、換回原本的「環繞」設定檔，並重新啟動 PipeWire 嗎？',
    out: '輸出', in: '輸入', mono: '單聲道', send_fail: '沒有送出：',
    inputs: '輸入', outputs: '輸出', gain: '增益', pan: 'Pan', dsp: 'DSP',
    main_vol: 'Main 音量', blend: '監聽比例', blend_tip: 'Main 裡輸入／電腦播放的音量（dB）。和前面板的 blend 是同一個值。用喇叭時把它轉到播放那側，麥克風才不會進喇叭。', phones_vol: '耳機音量', phones_mute: '耳機靜音', mono: '單聲道',
    rv_mix: '乾濕比', rv_pre: '預延遲', rv_size: '大小', rv_hp: '低切', rv_amount: 'Dry/Wet', rv_adv: '進階：reverb 本身的設定',
    rv_ambience: 'Ambience', rv_room: 'Room', rv_studio: 'Studio', rv_club: 'Club', rv_plate: 'Plate', rv_hall: 'Hall', rv_theatre: 'Theatre', rv_arena: 'Arena',
    rv_note: '八種風格，用 io44 reverb 能調的長度、預延遲、低切做出來。量在 50% 是該風格的建議量；0 是不送。混音裡的 Reverb 推桿決定各混音聽到多少。',
    rv_note_pub: '照這一家公開的預設數值，換算成 io44 reverb 能調的長度、預延遲、低切；亮暗、初期反射、高切做不到，所以接近但不一樣。量在 50% 是該風格的建議量。',
    preset_lead: '一鍵套用：', preset_talk: '說話', preset_sing: '唱歌', preset_note_mic1: '說話照 stream-mic 的說話（指向），唱歌照它的唱歌；唱歌會打開 reverb、說話關掉（reverb 兩支麥共用）。增益不動，壓縮器的門檻和補償也會換成預設的值。', preset_note_headset: '說話照 stream-mic 的說話（無指向），唱歌照它的唱歌；唱歌會打開 reverb、說話關掉（reverb 兩支麥共用）。增益不動，壓縮器的門檻和補償也會換成預設的值。',
    fam_ours: '標準', fam_y: 'Y 家', fam_d: 'D 家', fam_f: 'F 家', eq_natural: '自然', eq_demud: '去悶', eq_custom: '目前是自訂的值。',
    eq_style_note: '選一個風格當起點（會打開 EQ 和低切）；改了數值就是自訂。',
    eq_style_pub: '這一家公開的預設數值：中頻、Presence 照原本的頻率和 Q；最低、最高那段換成我們的 Low、Air 架形，所以接近但不完全一樣。',
    rv_custom: '自訂：進階設定改過，不是哪一種風格了。按一種風格回到它的設定。',
    io_note: '增益和 Main 音量是 io44 回報的實際值；其他項目 io44 不回報，顯示的是這台電腦保存的設定（耳機音量設定過才會知道）。DSP 關掉時麥克風不經過處理。',
    rate_title: '取樣率', rate_auto: '跟系統', rate_running: '目前', rate_idle: '閒置中',
    rate_note: 'io44 開啟時用的取樣率。和系統不同時，PipeWire 會自動轉換。切換會重新啟動 PipeWire，聲音會中斷一下。',
    rate_confirm: '要把 io44 的取樣率改成 {r}，並重新啟動 PipeWire 嗎？',
    rate_confirm_win: '要把 io44 的取樣率改成 {r} 嗎？錄音和播放會中斷一下。',
    rate_note_win: 'io44 的取樣率，透過它的 USB 音訊驅動程式設定。切換時錄音和播放會中斷一下。',
    rec: '錄處理後', rec_small: '關：錄音裝置和 Stream Mix 收到處理前的原音',
    phantom: '48V', phantom_small: '幻象電源（只有 Mic 1）', phantom_confirm: '要打開 Mic 1 的 48V 幻象電源嗎？\n鋁帶麥克風和真空管麥克風可能會被 48V 損壞，請確認接的是需要 48V 的電容麥克風。',
    fat: '處理',
    f_lowcut: 'Low Cut', f_gate: 'Gate', f_comp: 'Compressor', f_eq: 'EQ', f_limit: 'Limiter',
    f_freq: '頻率', f_on: '開', f_expander: 'Expander', f_threshold: 'Threshold', f_range: 'Range', f_attack: 'Attack', f_hold: 'Hold', f_release: 'Release',
    f_ratio: 'Ratio', f_knee: 'Knee', f_makeup: 'Makeup', f_ceiling: 'Ceiling', f_low: 'Low (200 Hz)', f_mid: 'Mid', f_mid_f: 'Mid frequency', f_mid_q: 'Mid Q', f_pres_q: 'Presence Q', f_pres: 'Presence', f_pres_f: 'Presence frequency', f_air: 'Air (10 kHz)',
    fat_note: '和 stream-mic 相同的處理鏈與範圍，由 io44 的 DSP 執行。點一段看細節，亮燈是開著；改一個值時只重送那一段。',
    f_eq_note: '拖曳圓點：Mid、Presence 左右移動頻率也上下調增益，Low、Air 上下調增益（shelf 的點在一半增益處）。滑鼠停在 Mid 或 Presence 上轉滾輪調 Q。Low Cut 是處理鏈最前面的一段，不在這張圖裡。',
    f_lc_note: '左右拖曳圓點調頻率（每八度 12 dB）。Low Cut 在處理鏈最前面，Gate 和 Compressor 之前。',
    f_bypassed: 'DSP 關：聽不到這些設定', f_dsp_on: 'DSP 開',
    f_voicefx: '聲音效果', fx_model: '效果', fx_low: '低頻', fx_width: '寬度', fx_mix: '混合', fx_ctype: '載波', fx_cfreq: '載波頻率',
    fx_vol: '音量', fx_c2: '第二載波', fx_c2freq: '第二載波頻率', fx_dist: '失真', fx_tune: '音高', fx_fb: '回授', fx_damp: '阻尼', fx_time: '時間',
    fx_semi: '降低（半音）', noise: '噪音', saw: '鋸齒波', square: '方波',
    fx_note: '只有 Mic 1 有聲音效果，一次一種。換效果時參數從我們的起始值開始，切換約需 1 秒。',
  },
  en: {
    connected: 'Connected', offline: 'io44 not connected', main_knob: 'Main knob', unknown: 'Unknown', off: 'Off',
    mute: 'Mute', muted: 'Muted', bus_main: 'Main', bus_a: 'Stream Mix A', bus_b: 'Stream Mix B',
    note_main: 'The mix in the speakers and headphones.', note_a: 'Capture channels 5–6 (for the stream, Discord).', note_b: 'Capture channels 7–8 (a second stream mix).',
    unknown_note: 'The io44 does not report its mixes, so this computer keeps all the settings and writes them whenever the io44 is there. The first time they start neutral (every input into every mix at 0 dB, the gains and the blend as the io44 has them). Drag a fader, scroll, or use the arrow keys (Shift for fine steps); double-click for 0 dB.',
    k_input: 'Input', k_playback: 'Computer', k_fx: 'Effect', bus_out: 'Out',
    pw_title: 'Names in PipeWire', pw_on: 'Installed', pw_offstate: 'Not installed',
    pw_note: 'By default Linux sees the io44 as “Analog Surround 2.1 out / 7.1 in”: all 8 inputs in one device, and Virtual A/B unreachable. Installing splits it into the named devices below. Installing and removing restart PipeWire: sound stops for a moment.',
    pw_install: 'Install', pw_remove: 'Remove', pw_working: 'Working…',
    pw_confirm_install: 'Restart PipeWire and make “io44 Playback” the default output?',
    pw_confirm_remove: 'Remove the configuration, go back to the “Surround” profile, and restart PipeWire?',
    out: 'Output', in: 'Input', mono: 'mono', send_fail: 'Not sent: ',
    inputs: 'Inputs', outputs: 'Outputs', gain: 'Gain', pan: 'Pan', dsp: 'DSP',
    main_vol: 'Main volume', blend: 'Blend', blend_tip: 'The inputs’ / the playback’s level in Main (dB). The same value as the front panel’s blend. With speakers, keep it toward playback so the mic stays out of them.', phones_vol: 'Headphones', phones_mute: 'Headphones mute', mono: 'Mono',
    rv_mix: 'Wet/dry', rv_pre: 'Pre-delay', rv_size: 'Size', rv_hp: 'Low cut', rv_amount: 'Amount (dry/wet)', rv_adv: 'Advanced: the reverb’s own settings',
    rv_ambience: 'Ambience', rv_room: 'Room', rv_studio: 'Studio', rv_club: 'Club', rv_plate: 'Plate', rv_hall: 'Hall', rv_theatre: 'Theatre', rv_arena: 'Arena',
    rv_note: 'Eight styles, made from what the io44’s reverb lets one set: length, pre-delay, low cut. At 50% the amount is the style’s own; 0 sends nothing. The Reverb fader in each mix sets how much that mix gets.',
    rv_note_pub: 'This maker’s published preset values, turned into what the io44’s reverb can set (length, pre-delay, low cut): its brightness, early reflections and high cut cannot be had, so close, not the same. At 50% the amount is the style’s own.',
    preset_lead: 'One click:', preset_talk: 'Talk', preset_sing: 'Sing', preset_note_mic1: 'Talk as stream-mic’s Talk (directional), Sing as its Sing; Sing turns the reverb on, Talk off (both mics share it). The gain stays; the compressor’s threshold and makeup take the preset’s values too.', preset_note_headset: 'Talk as stream-mic’s Talk (omni), Sing as its Sing; Sing turns the reverb on, Talk off (both mics share it). The gain stays; the compressor’s threshold and makeup take the preset’s values too.',
    fam_ours: 'Standard', fam_y: 'Y', fam_d: 'D', fam_f: 'F', eq_natural: 'Natural', eq_demud: 'De-mud', eq_custom: 'Custom values. ',
    eq_style_note: 'A style to start from (it switches the EQ and the low cut on); changing a value makes it custom.',
    eq_style_pub: 'This maker’s published preset values: the mid and presence bells at their own frequency and Q, their lowest and highest on our Low and Air shelves, so near, not the same.',
    rv_custom: 'Custom: the advanced settings were changed. Pick a style to go back to its settings.',
    io_note: 'Gain and Main volume are what the io44 reports; it does not report the rest, which shows the settings this computer keeps (the headphones are known once set here). With DSP off the mic is not processed.',
    rate_title: 'Sample rate', rate_auto: 'System', rate_running: 'Now', rate_idle: 'idle',
    rate_note: 'The rate the io44 is opened at. When the system runs at another rate, PipeWire converts. Changing it restarts PipeWire: sound stops for a moment.',
    rate_confirm: 'Set the io44 to {r} and restart PipeWire?',
    rate_confirm_win: 'Set the io44 to {r}? Recording and playback stop for a moment.',
    rate_note_win: 'The io44’s sample rate, set through its USB audio driver. Recording and playback stop for a moment when it changes.',
    rec: 'Record processed', rec_small: 'off: the recording device and the stream mixes get the sound before the processing',
    phantom: '48V', phantom_small: 'phantom power (Mic 1 only)', phantom_confirm: 'Turn on 48V phantom power on Mic 1?\nRibbon and tube mics can be damaged by it: make sure a condenser mic that needs it is plugged in.',
    fat: 'Processing',
    f_lowcut: 'Low Cut', f_gate: 'Gate', f_comp: 'Compressor', f_eq: 'EQ', f_limit: 'Limiter',
    f_freq: 'Frequency', f_on: 'On', f_expander: 'Expander', f_threshold: 'Threshold', f_range: 'Range', f_attack: 'Attack', f_hold: 'Hold', f_release: 'Release',
    f_ratio: 'Ratio', f_knee: 'Knee', f_makeup: 'Makeup', f_ceiling: 'Ceiling', f_low: 'Low (200 Hz)', f_mid: 'Mid', f_mid_f: 'Mid frequency', f_mid_q: 'Mid Q', f_pres_q: 'Presence Q', f_pres: 'Presence', f_pres_f: 'Presence frequency', f_air: 'Air (10 kHz)',
    fat_note: 'stream-mic’s processing chain and ranges, run by the io44’s DSP. Click a part for its details; a lit lamp is on. A change sends that part only.',
    f_eq_note: 'Drag the points: Mid and Presence both ways (frequency and gain), Low and Air up and down (a shelf’s point sits at half its gain). The wheel over Mid or Presence sets its Q. The Low Cut is the chain’s first stage, not in this curve.',
    f_lc_note: 'Drag the point left or right for the frequency (12 dB per octave). The Low Cut is first in the chain, before the gate and the compressor.',
    f_bypassed: 'DSP off: none of this is heard', f_dsp_on: 'DSP on',
    f_voicefx: 'Voice FX', fx_model: 'Effect', fx_low: 'Lows', fx_width: 'Width', fx_mix: 'Mix', fx_ctype: 'Carrier', fx_cfreq: 'Carrier',
    fx_vol: 'Volume', fx_c2: 'Second carrier', fx_c2freq: 'Its frequency', fx_dist: 'Distortion', fx_tune: 'Tune', fx_fb: 'Feedback', fx_damp: 'Damping', fx_time: 'Time',
    fx_semi: 'Down (semitones)', noise: 'Noise', saw: 'Saw', square: 'Square',
    fx_note: 'Only Mic 1 has voice effects, one at a time. A new effect starts at our values; switching takes about a second.',
  },
};
let LANG = 'zh';
try { LANG = localStorage.getItem('io44.lang') || (/^zh/i.test(navigator.language || '') ? 'zh' : 'en'); } catch (e) { LANG = /^zh/i.test(navigator.language || '') ? 'zh' : 'en'; }
const t = (k) => I18N[LANG][k] ?? k;
const $ = (id) => document.getElementById(id);

// the sources in the order of the device's front panel, with the meter that shows each (a "?" meter is a reading
// not yet confirmed on the device, drawn fainter)
const SOURCES = [
  { id: 3, name: 'Mic 1', kind: 'k_input', meter: 'mic1' },
  { id: 4, name: 'Headset', kind: 'k_input', meter: 'mic2?' },
  { id: 6, name: 'Line In', kind: 'k_input', meter: 'line?' },
  { id: 0, name: 'Playback', kind: 'k_playback', meter: 'playback' },
  { id: 1, name: 'Virtual A', kind: 'k_playback', meter: 'virtual-a' },
  { id: 2, name: 'Virtual B', kind: 'k_playback', meter: 'virtual-b' },
  { id: 5, name: 'Reverb', kind: 'k_fx', meter: 'fx?' },
];
const BUSES = [{ id: 0, key: 'bus_main', note: 'note_main', meter: 'main' }, { id: 1, key: 'bus_a', note: 'note_a', meter: 'stream-a' }, { id: 2, key: 'bus_b', note: 'note_b', meter: 'stream-b' }];
const PW = [['out', 'io44 Playback', ''], ['out', 'io44 Virtual A', ''], ['out', 'io44 Virtual B', ''], ['in', 'io44 Mic 1', 'mono'], ['in', 'io44 Headset', 'mono'],
  ['in', 'io44 Line In', ''], ['in', 'io44 Stream Mix A', ''], ['in', 'io44 Stream Mix B', '']];

let S = { mix: {}, pipewire: false, connected: false };
let bus = 0;
try { bus = +(localStorage.getItem('io44.bus') || 0); } catch (e) { /* private window */ }

// ------------------------------------------------------------------ the fader's law: position 0..1 <-> dB
// off at the bottom, then -60 / -20 / 0 / +10 at fixed points, linear in dB between them (0 dB at three quarters)
const LAW = [[0.04, -60], [0.38, -20], [0.75, 0], [1, 10]];
function posToDb(p) {
  if (p < 0.02) return -145;
  if (p <= LAW[0][0]) return -60;
  for (let i = 1; i < LAW.length; i++) if (p <= LAW[i][0]) { const [p0, d0] = LAW[i - 1], [p1, d1] = LAW[i]; return d0 + (d1 - d0) * (p - p0) / (p1 - p0); }
  return 10;
}
function dbToPos(d) {
  if (d <= -100) return 0;
  if (d <= -60) return LAW[0][0];
  for (let i = 1; i < LAW.length; i++) if (d <= LAW[i][1]) { const [p0, d0] = LAW[i - 1], [p1, d1] = LAW[i]; return p0 + (p1 - p0) * (d - d0) / (d1 - d0); }
  return 1;
}
const fmtDb = (d) => (d <= -100 ? t('off') : (d > 0.05 ? '+' : '') + d.toFixed(1) + ' dB');
const roundDb = (d) => (d <= -100 ? -145 : Math.round(d * 2) / 2);

// ------------------------------------------------------------------ talking to the server
async function api(path, body) {
  const r = await fetch(path, body ? { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) } : {});
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.status);
  return j;
}
function value(src) { const b = S.mix[String(bus)]; return b && String(src) in b ? b[String(src)] : null; }

// one request in flight per fader, the newest value waiting: dragging never queues up
const pending = new Map();
function send(src, d) {
  const key = bus + ':' + src;
  const p = pending.get(key);
  if (p) { p.next = d; return; }
  const job = { next: null };
  pending.set(key, job);
  const go = (v) => api('/api/mix', { bus, source: src, db: v }).then(() => {
    (S.mix[String(bus)] ||= {})[String(src)] = v; banner('');
  }).catch((e) => banner(t('send_fail') + e.message)).finally(() => {
    if (job.next !== null) { const n = job.next; job.next = null; go(n); } else pending.delete(key);
  });
  go(d);
}

// ------------------------------------------------------------------ inputs, outputs, reverb: one row per setting
const INPUTS = [{ key: 'mic1', ch: 0, name: 'Mic 1', lo: 0, hi: 60 }, { key: 'headset', ch: 1, name: 'Headset', lo: 0, hi: 30 }, { key: 'line', ch: 2, name: 'Line In', lo: -12, hi: 12 }];
let DEV = null;            // what the io44 reports (gains, Main volume), from the meter polls
const held = new Set();    // controls being dragged: their value is not overwritten by the polls
const setting = (what, key) => { const v = (S.set || {})[what]; return v === undefined ? undefined : key ? (v || {})[key] : v; };
const busy = new Map();
function sendSet(what, key, value) {
  const k = what + ':' + key;
  const p = busy.get(k);
  if (p) { p.next = value; return; }
  const job = { next: undefined };
  busy.set(k, job);
  const go = (v) => api('/api/set', { what, key, value: v }).then((r) => {
    S.set ||= {};
    if (what !== 'gain' && what !== 'main-volume') { if (key) (S.set[what] ||= {})[key] = r.value; else S.set[what] = r.value; }
    banner('');
  }).catch((e) => banner(t('send_fail') + e.message)).finally(() => {
    if (job.next !== undefined) { const n = job.next; job.next = undefined; go(n); } else { busy.delete(k); ioRender(); }
  });
  go(value);
}
function lvl(id, label, lo, hi, step) {
  return '<label class="lvl"><span>' + label + '</span><input type="range" id="' + id + '" min="' + lo + '" max="' + hi + '" step="' + step + '"><output id="' + id + 'V"></output></label>';
}
function sw(id, label, small) { return '<div class="swrow"><span class="lab">' + label + (small ? '<small>' + small + '</small>' : '') + '</span><button class="sw" role="switch" id="' + id + '"></button></div>'; }
// the monitor blend as the two sides' gains in Main (ucstate.blend_gains): inputs | playback
const fmtBlend = (p) => { const g = (x) => (x <= 0 ? t('off') : (20 * Math.log10(Math.min(1, x))).toFixed(0)); return g(1 - p) + ' / ' + g(1 + p); };
const fmtPan = (v) => (Math.abs(v) < 0.025 ? 'C' : (v < 0 ? 'L' : 'R') + Math.round(Math.abs(v) * 100));
// edit: how its value is typed (numedit.js rangeEdit's extras), false for none
function wireRange(id, onMove, fmt, edit) {
  const el = $(id);
  if (edit !== false && typeof rangeEdit === 'function') rangeEdit(id, edit);
  el.addEventListener('pointerdown', () => held.add(id));
  el.addEventListener('input', () => { held.add(id); el.classList.remove('unknown'); $(id + 'V').textContent = fmt(+el.value); $(id + 'V').classList.remove('unknown'); onMove(+el.value); });
  el.addEventListener('change', () => held.delete(id));
}
function showRange(id, v, fmt) {
  if (held.has(id) || $(id + 'V').dataset.editing === '1') return;
  const known = v !== undefined && v !== null;
  if (known) $(id).value = v;
  $(id + 'V').textContent = known ? fmt(v) : t('unknown');
  $(id + 'V').classList.toggle('unknown', !known);
  $(id).classList.toggle('unknown', !known);
}
// a switch the io44 does not report and that was never set from here is neither on nor off: the knob in the middle
// (it looked off, while the reverb, say, was running)
function showSw(id, v) {
  const unknown = v === undefined;
  $(id).setAttribute('aria-checked', unknown ? 'mixed' : String(!!v));
  $(id).classList.toggle('unknown', unknown);
  $(id).title = unknown ? t('unknown') : '';
}

// ------------------------------------------------------------------ the mics' processing (a card of its own)
// Laid out as stream-mic's processing chain, with its parts and ranges (settings.FAT_KEYS): a module per part (its
// value and a lamp for on), the picked one's details below; the EQ also as its response curve, its points dragged up
// and down (the low cut's left and right). [key, label, kind, lo, hi, format]: 'sw' a switch, 'lin'/'log' a slider
// (log for frequencies and times), 'step' buttons (lo = how many, hi = their labels). Times are in ms.
const msv = (v) => (v < 10 ? (+v).toFixed(1) : Math.round(v)) + ' ms';
const hz = (v) => (v >= 1000 ? (v / 1000).toFixed(v >= 10000 ? 1 : 2) + ' kHz' : Math.round(v) + ' Hz');
const dbv = (v) => (v > 0.05 ? '+' : '') + (+v).toFixed(1) + ' dB';
const FAT = {
  lowcut: [['freq', 'f_freq', 'log', 40, 400, hz]],
  eq: [['low', 'f_low', 'lin', -6, 6, dbv], ['mid', 'f_mid', 'lin', -6, 6, dbv], ['mid_f', 'f_mid_f', 'log', 200, 1000, hz], ['mid_q', 'f_mid_q', 'log', 0.5, 4, (v) => (+v).toFixed(2)], ['pres', 'f_pres', 'lin', -6, 6, dbv], ['pres_f', 'f_pres_f', 'log', 2000, 6000, hz], ['pres_q', 'f_pres_q', 'log', 0.5, 4, (v) => (+v).toFixed(2)], ['air', 'f_air', 'lin', -6, 6, dbv]],
  gate: [['threshold', 'f_threshold', 'lin', -80, -20, dbv], ['range', 'f_range', 'lin', 3, 80, (v) => Math.round(v) + ' dB'],
    ['attack', 'f_attack', 'log', 0.1, 50, msv], ['hold', 'f_hold', 'lin', 1, 300, msv], ['release', 'f_release', 'log', 40, 2000, msv],
    ['expander', 'f_expander', 'sw']],
  comp: [['threshold', 'f_threshold', 'lin', -40, -6, dbv], ['ratio', 'f_ratio', 'lin', 1, 8, (v) => (+v).toFixed(1) + ':1'],
    ['knee', 'f_knee', 'lin', 0, 12, (v) => (+v).toFixed(1) + ' dB'], ['attack', 'f_attack', 'log', 1, 40, msv],
    ['release', 'f_release', 'log', 30, 400, msv], ['makeup', 'f_makeup', 'lin', 0, 18, dbv]],
  limit: [['ceiling', 'f_ceiling', 'lin', -12, 0, dbv], ['release', 'f_release', 'log', 20, 200, msv]],
};
// Mic 1's voice effects (settings.VOICE_KEYS)
const pct = (v) => Math.round(v * 100) + '%';
const hz2 = (v) => (v < 10 ? (+v).toFixed(2) + ' Hz' : hz(v));
const VFX_NAMES = { 0: 'Doubler', 1: 'Detune', 2: 'Robot A', 3: 'Robot B', 4: 'Robot C', 5: 'Echo' };
const MIXK = ['mix', 'fx_mix', 'lin', 0, 1, pct];
const VFX = {
  0: [['low', 'fx_low', 'lin', 0, 1, (v) => '+' + (9 * v).toFixed(1) + ' dB'], ['width', 'fx_width', 'lin', 0, 1, pct], MIXK],
  1: [['semitones', 'fx_semi', 'step', 9, ['0', '-1', '-2', '-3', '-4', '-5', '-6', '-7', '-8']], MIXK],
  2: [['carrier', 'fx_ctype', 'step', 3, ['noise', 'saw', 'square']], ['freq', 'fx_cfreq', 'log', 50, 500, hz], ['volume', 'fx_vol', 'lin', 0, 1, pct], MIXK],
  3: [['freq', 'fx_cfreq', 'log', 0.1, 2000, hz2], ['distortion', 'fx_dist', 'lin', 0, 1, pct], ['volume', 'fx_vol', 'lin', 0, 1, pct],
    ['freq2_on', 'fx_c2', 'sw'], ['freq2', 'fx_c2freq', 'log', 0.1, 2000, hz2], MIXK],
  4: [['tune', 'fx_tune', 'lin', 250, 1550, hz], ['feedback', 'fx_fb', 'lin', 0.5, 0.85, pct], ['damping', 'fx_damp', 'lin', 0.3, 0.9, pct],
    ['distortion', 'fx_dist', 'lin', 0, 1, pct], ['volume', 'fx_vol', 'lin', 0, 1, pct], MIXK],
  5: [['time', 'fx_time', 'log', 0.01, 0.25, (v) => Math.round(v * 1000) + ' ms'], ['feedback', 'fx_fb', 'lin', 0, 0.45, pct], MIXK],
};
const secsOf = (m) => ['lowcut', 'gate', 'comp', 'eq', 'limit'].concat(m === 'mic1' ? ['voicefx'] : []);
let SECS = secsOf('mic1');
let FM = 'mic1', FPICK = 'eq';
const F = () => (S.fat ? S.fat[FM] : null);
const toPos = (it, v) => (it[2] === 'log' ? 1000 * Math.log(v / it[3]) / Math.log(it[4] / it[3]) : v);
const fromPos = (it, p) => (it[2] === 'log' ? it[3] * Math.pow(it[4] / it[3], p / 1000) : +p);
const round = (v) => +(+v).toPrecision(4);
function secOn(sec, f) { return !!f && !!f[sec].on; }
function secSub(sec, f) {
  if (!f) return '–';
  const x = f[sec];
  if (sec === 'lowcut') return hz(x.freq);
  if (sec === 'gate') return dbv(x.threshold);
  if (sec === 'comp') return dbv(x.threshold) + ' · ' + (+x.ratio).toFixed(1) + ':1';
  if (sec === 'eq') return [x.low, x.mid ?? 0, x.pres, x.air].map((v) => (v > 0 ? '+' : '') + (+v).toFixed(1)).join(' / ');
  if (sec === 'voicefx') return VFX_NAMES[x.model] || '–';
  return dbv(x.ceiling);
}
const fatBusy = new Map();
function sendFat(sec, key, value) {
  const m = FM, k = m + sec + key, p = fatBusy.get(k);
  if (S.fat) S.fat[m][sec][key] = value;  // drawn at once, confirmed by the reply
  if (p) { p.next = value; return; }
  const job = { next: undefined }; fatBusy.set(k, job);
  const go = (v) => api('/api/fat', { input: m, section: sec, key, value: v }).then((r) => { S.fat[m][sec][key] = r.value; banner(''); })
    .catch((e) => banner(t('send_fail') + e.message)).finally(() => {
      if (job.next !== undefined) { const n = job.next; job.next = undefined; go(n); } else { fatBusy.delete(k); fatRender(); }
    });
  go(value);
}
function rowHtml(it, id) {
  if (it[2] === 'sw') return sw(id, t(it[1]));
  if (it[2] === 'step') return '<div class="lvl"><span>' + t(it[1]) + '</span><div class="seg steps" id="' + id + '">' + it[4].map((l, n) => '<button data-v="' + n + '">' + t(l) + '</button>').join('') + '</div><output></output></div>';
  return it[2] === 'log' ? lvl(id, t(it[1]), 0, 1000, 1) : lvl(id, t(it[1]), it[3], it[4], it[4] - it[3] <= 1 ? 0.01 : 0.5);
}
function wireRow(it, id, sec) {
  const el = $(id);
  if (it[2] === 'sw') el.onclick = () => F() && sendFat(sec, it[0], F()[sec][it[0]] ? 0 : 1);
  else if (it[2] === 'step') for (const b of el.children) b.onclick = () => F() && sendFat(sec, it[0], +b.dataset.v);
  else wireRange(id, (p) => { if (F()) { sendFat(sec, it[0], round(fromPos(it, p))); if (sec === 'eq' || sec === 'lowcut') drawFatEq(); } }, (p) => it[5](fromPos(it, p)), fatEdit(it, sec));
}
// a processing value typed: in the units it is shown in (percent, ms), to its slider's steps (log ones: 1 Hz under
// 1 kHz and 10 Hz above, 0.1 ms under 10 ms and 1 ms above, Q 0.05), sent as the setting
function fatEdit(it, sec) {
  const scale = it[5] === pct ? 100 : sec === 'voicefx' && it[0] === 'time' ? 1000 : 1;
  const ms = it[5] === msv || scale === 1000;
  const snap = it[2] !== 'log' ? null : it[0].endsWith('_q') ? (v) => Math.round(v * 20) / 20
    : ms ? (v) => (v < 10 ? Math.round(v * 10) / 10 : Math.round(v)) : (v) => (v < 10 ? Math.round(v * 100) / 100 : v < 1000 ? Math.round(v) : Math.round(v / 10) * 10);
  return { lo: it[3] * scale, hi: it[4] * scale, step: it[4] - it[3] <= 1 ? 0.01 * scale : 0.5, snap, unit: ms ? 'ms' : undefined,
    get: () => (F() ? F()[sec][it[0]] * scale : undefined),
    apply: (v) => { if (!F()) return; sendFat(sec, it[0], round(v / scale)); fatRender(); if (sec === 'eq' || sec === 'lowcut') drawFatEq(); } };
}
function showRow(it, id, v) {
  if (!$(id)) return;
  if (it[2] === 'sw') showSw(id, v === undefined ? undefined : !!v);
  else if (it[2] === 'step') for (const b of $(id).children) b.setAttribute('aria-pressed', String(+b.dataset.v === v));
  else showRange(id, v === undefined ? undefined : toPos(it, v), (p) => it[5](fromPos(it, p)));
}
const knobsOf = (sec) => (sec === 'voicefx' ? VFX[(F() && F().voicefx || {}).model] || [] : FAT[sec]);
let BUILT = '';
function fatBuild() {
  $('fatMic').innerHTML = INPUTS.slice(0, 2).map((c) => '<button data-m="' + c.key + '">' + c.name + '</button>').join('');
  $('fatMic').onclick = (e) => {
    const b = e.target.closest('button'); if (!b || b.dataset.m === FM) return;
    FM = b.dataset.m; SECS = secsOf(FM); if (!SECS.includes(FPICK)) FPICK = 'eq';
    chainBuild(); fatDetailBuild(); fatRender();
  };
  $('fatPreset').innerHTML = ['talk', 'sing'].map((p) => '<button data-p="' + p + '">' + t('preset_' + p) + '</button>').join('');
  $('fatPreset').onclick = async (e) => {
    const b = e.target.closest('button'); if (!b) return;
    try { await api('/api/set', { what: 'preset', key: FM, value: b.dataset.p }); S = await api('/api/state'); banner(''); } catch (x) { banner(t('send_fail') + x.message); }
    fatDetailBuild(); fatRender(); if (typeof render === 'function') render();
  };
  chainBuild();
  $('fatChain').onclick = (e) => { const m = e.target.closest('.mod'); if (m) { FPICK = m.dataset.s; fatDetailBuild(); fatRender(); } };
  fatDetailBuild();
}
function chainBuild() {
  $('fatChain').style.gridTemplateColumns = 'repeat(' + SECS.length + ', minmax(0, 1fr))';
  $('fatChain').innerHTML = SECS.map((sec) => '<button class="mod" data-s="' + sec + '"><div class="name">' + t('f_' + sec) + '</div><div class="meta"><span class="sub"></span><span class="led"></span></div><span class="arrow"></span></button>').join('');
}
// the EQ's styles (settings.EQ_STYLES): ours, and "f" (Focusrite Vocaster's published Enhance presets)
const EQ_FAMILIES = [['ours', [['natural', 'eq_natural'], ['demud', 'eq_demud']]], ['f', [['f-clean', 'Clean'], ['f-warm', 'Warm'], ['f-bright', 'Bright'], ['f-radio', 'Radio']]]];
let eqFam = null;
async function eqStyle(name) {
  try { await api('/api/fat', { input: FM, section: 'eq', key: 'style', value: name }); S = await api('/api/state'); banner(''); } catch (e) { banner(t('send_fail') + e.message); }
  fatRender();
}
async function voiceModel(m) {
  try { await api('/api/fat', { input: 'mic1', section: 'voicefx', key: 'model', value: m }); S = await api('/api/state'); banner(''); } catch (e) { banner(t('send_fail') + e.message); }
  fatDetailBuild(); fatRender();
}
function fatDetailBuild() {
  const sec = FPICK, d = $('fatDetail');
  let h = '<div class="dh"><b>' + t('f_' + sec) + '</b><span class="spacer"></span><label>' + t('f_on') + '<button class="sw" role="switch" id="fd_on"></button></label></div>';
  if (sec === 'eq') h += '<div class="seg" id="eqFam" style="margin-top:8px">' + EQ_FAMILIES.map(([f]) => '<button data-f="' + f + '">' + t('fam_' + f) + '</button>').join('') + '</div>' +
    '<div class="seg steps rvstyles" id="eqStyles" style="margin-top:6px"></div><p class="note" id="eqStyleNote"></p>';
  if (sec === 'eq' || sec === 'lowcut') h += '<canvas id="fatEq"></canvas><p class="note">' + t(sec === 'eq' ? 'f_eq_note' : 'f_lc_note') + '</p>';
  if (sec === 'voicefx') h += '<div class="lvl"><span>' + t('fx_model') + '</span><div class="seg steps" id="fd_model">' + Object.entries(VFX_NAMES).map(([m, n]) => '<button data-v="' + m + '">' + n + '</button>').join('') + '</div><output></output></div>';
  h += '<div class="pgrid">' + knobsOf(sec).map((it) => rowHtml(it, 'fd_' + it[0])).join('') + '</div>';
  if (sec === 'voicefx') h += '<p class="note">' + t('fx_note') + '</p>';
  d.innerHTML = h;
  $('fd_on').onclick = () => F() && sendFat(sec, 'on', F()[sec].on ? 0 : 1);
  if (sec === 'voicefx') for (const b of $('fd_model').children) b.onclick = () => voiceModel(+b.dataset.v);
  if (sec === 'eq') {
    $('eqFam').onclick = (e) => { const b = e.target.closest('button'); if (b) { eqFam = b.dataset.f; fatRender(); } };
    $('eqStyles').onclick = (e) => { const b = e.target.closest('button'); if (b) eqStyle(b.dataset.v); };
  }
  for (const it of knobsOf(sec)) wireRow(it, 'fd_' + it[0], sec);
  if ($('fatEq')) eqDrag($('fatEq'));
  BUILT = FM + sec + (sec === 'voicefx' ? (F() && F().voicefx || {}).model : '');
}
function fatRender() {
  const f = F();
  for (const b of $('fatMic').children) b.setAttribute('aria-pressed', String(b.dataset.m === FM));
  if ($('fatPresetNote')) $('fatPresetNote').textContent = t('preset_note_' + FM);
  for (const m of $('fatChain').children) {
    m.classList.toggle('on', secOn(m.dataset.s, f));
    m.setAttribute('aria-selected', String(m.dataset.s === FPICK));
    m.querySelector('.sub').textContent = secSub(m.dataset.s, f);
  }
  const dspOff = setting('dsp', FM) === false;
  $('fatDsp').textContent = dspOff ? t('f_bypassed') : t('f_dsp_on');
  $('fatDsp').className = 'chip' + (dspOff ? ' off' : ' ok');
  if (!f) return;
  const sec = FPICK;
  if (BUILT !== FM + sec + (sec === 'voicefx' ? f.voicefx.model : '')) fatDetailBuild();
  showSw('fd_on', !!f[sec].on);
  if (sec === 'voicefx') for (const b of $('fd_model').children) b.setAttribute('aria-pressed', String(+b.dataset.v === f.voicefx.model));
  for (const it of knobsOf(sec)) showRow(it, 'fd_' + it[0], f[sec][it[0]]);
  if (sec === 'eq' && $('eqFam')) {
    const cur = f.eq.style || '', fam = eqFam || (EQ_FAMILIES.find(([, l]) => l.some(([v]) => v === cur)) || ['ours'])[0];
    for (const b of $('eqFam').children) b.setAttribute('aria-pressed', String(b.dataset.f === fam));
    if ($('eqStyles').dataset.k !== fam + LANG) { $('eqStyles').dataset.k = fam + LANG; $('eqStyles').innerHTML = EQ_FAMILIES.find(([x]) => x === fam)[1].map(([v, n]) => '<button data-v="' + v + '">' + (n.startsWith('eq_') ? t(n) : n) + '</button>').join(''); }
    for (const b of $('eqStyles').children) b.setAttribute('aria-pressed', String(b.dataset.v === cur));
    $('eqStyleNote').textContent = (cur ? '' : t('eq_custom')) + t(fam === 'ours' ? 'eq_style_note' : 'eq_style_pub');
  }
  if ($('fatEq') && !eqHold) drawFatEq();
  if (typeof scopeRender === 'function') scopeRender();
}

// the EQ's curve (stream-mic's drawing): the low cut, the three bands (settings.EQ_BANDS) and the mid bell (moved both ways)
const FS = 48000;
const EQB = [['ls', 200, Math.SQRT1_2, 'low'], ['bell', 3000, 1, 'pres'], ['hs', 10000, Math.SQRT1_2, 'air']];
function biquadDb(kind, f0, q, gain, f) {
  const A = Math.pow(10, gain / 40), w0 = 2 * Math.PI * f0 / FS, cw = Math.cos(w0), al = Math.sin(w0) / (2 * q);
  let b, a;
  if (kind === 'hp') { b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]; a = [1 + al, -2 * cw, 1 - al]; }
  else if (kind === 'bell') { b = [1 + al * A, -2 * cw, 1 - al * A]; a = [1 + al / A, -2 * cw, 1 - al / A]; }
  else {
    const sg = kind === 'ls' ? 1 : -1, r = 2 * Math.sqrt(A) * al;
    b = [A * ((A + 1) - sg * (A - 1) * cw + r), sg * 2 * A * ((A - 1) - sg * (A + 1) * cw), A * ((A + 1) - sg * (A - 1) * cw - r)];
    a = [(A + 1) + sg * (A - 1) * cw + r, -sg * 2 * ((A - 1) + sg * (A + 1) * cw), (A + 1) + sg * (A - 1) * cw - r];
  }
  const w = 2 * Math.PI * f / FS, c1 = Math.cos(w), s1 = Math.sin(w), c2 = Math.cos(2 * w), s2 = Math.sin(2 * w);
  const mag = (k) => Math.hypot(k[0] + k[1] * c1 + k[2] * c2, k[1] * s1 + k[2] * s2);
  return 20 * Math.log10(mag(b) / mag(a));
}
// the curve of the section open (FPICK): the low cut alone, or the EQ's four bands alone (they are separate stages)
function fatResponse(f, x) {
  if (FPICK === 'lowcut') return x.lowcut.on ? biquadDb('hp', x.lowcut.freq, Math.SQRT1_2, 0, f) : 0;
  let d = 0;
  if (x.eq.on) { for (const [k, f0, q, key] of EQB) d += biquadDb(k, key === 'pres' ? x.eq.pres_f ?? f0 : f0, key === 'pres' ? x.eq.pres_q ?? q : q, x.eq[key], f); d += biquadDb('bell', x.eq.mid_f ?? 400, x.eq.mid_q ?? 1.4, x.eq.mid ?? 0, f); }
  return d;
}
function fatPoints(x) {
  if (FPICK === 'lowcut') return [{ id: 'lowcut', name: t('f_lowcut'), f: x.lowcut.freq, g: 0, on: !!x.lowcut.on }];
  return [].concat(EQB.map(([k, f0, q, key]) => ({
    id: key, name: t('f_' + key), f: key === 'pres' ? x.eq.pres_f ?? f0 : f0, g: k === 'bell' ? x.eq[key] : x.eq[key] / 2, on: !!x.eq.on, half: k !== 'bell' })),
    [{ id: 'mid', name: t('f_mid'), f: x.eq.mid_f ?? 400, g: x.eq.mid ?? 0, on: !!x.eq.on }]);
}
function fitCanvas(c) {
  const r = c.getBoundingClientRect(), d = devicePixelRatio || 1;
  const w = Math.max(1, Math.round(r.width * d)), h = Math.max(1, Math.round(r.height * d));
  if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
  const g = c.getContext('2d'); g.setTransform(d, 0, 0, d, 0, 0);
  return [g, r.width, r.height];
}
const cssv = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const MONO = '"JetBrains Mono", ui-monospace, monospace', UIF = '"Inter", "Noto Sans TC", system-ui, sans-serif';
let eqGeo = null, eqHold = null;
function drawFatEq() {
  const c = $('fatEq'), x = F(); if (!c || !x) return;
  const [g, w, h] = fitCanvas(c);
  const fx = (f) => 30 + ((Math.log10(f) - Math.log10(20)) / 3) * (w - 40);
  const dy = (d) => h / 2 - (d / 12) * (h / 2 - 14);
  g.fillStyle = cssv('--inset'); g.fillRect(0, 0, w, h);
  g.font = '10px ' + MONO; g.textAlign = 'center';
  for (const f of [50, 100, 200, 500, 1000, 2000, 5000, 10000]) { g.fillStyle = 'rgba(255,255,255,.04)'; g.fillRect(Math.round(fx(f)), 0, 1, h); g.fillStyle = cssv('--faint'); g.fillText(f >= 1000 ? f / 1000 + 'k' : f, fx(f), h - 4); }
  g.textAlign = 'left';
  for (const d of [12, 6, 0, -6, -12]) { g.fillStyle = d === 0 ? 'rgba(255,255,255,.09)' : 'rgba(255,255,255,.04)'; g.fillRect(30, Math.round(dy(d)), w - 40, 1); g.fillStyle = cssv('--faint'); g.fillText((d > 0 ? '+' : '') + d, 4, dy(d) + 3); }
  g.beginPath();
  for (let i = 0; i <= 300; i++) { const f = 20 * Math.pow(1000, i / 300), y = dy(Math.max(-14, Math.min(14, fatResponse(f, x)))); i ? g.lineTo(fx(f), y) : g.moveTo(fx(f), y); }
  g.strokeStyle = cssv('--accent'); g.lineWidth = 2; g.stroke();
  g.lineTo(fx(20000), h); g.lineTo(fx(20), h); g.fillStyle = 'rgba(79,214,180,.08)'; g.fill();
  for (const p of fatPoints(x)) {
    const px = fx(p.f), py = dy(p.g);
    g.beginPath(); g.arc(px, py, 7, 0, 7); g.fillStyle = cssv('--panel2'); g.fill(); g.strokeStyle = p.on ? cssv('--accent') : cssv('--faint'); g.lineWidth = 2; g.stroke();
    g.fillStyle = p.on ? cssv('--muted') : cssv('--faint'); g.font = '11px ' + UIF; g.textAlign = 'center'; g.fillText(p.name, px, py - 12);
  }
  eqGeo = { fx, dy, w, h };
}
function eqDrag(c) {
  drawFatEq();
  const pos = (e) => { const r = c.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
  const near = (x, y) => F() && eqGeo && fatPoints(F()).find((p) => Math.hypot(eqGeo.fx(p.f) - x, eqGeo.dy(p.g) - y) < 14);
  c.addEventListener('pointerdown', (e) => { const [x, y] = pos(e); eqHold = near(x, y) || null; if (eqHold) c.setPointerCapture(e.pointerId); });
  c.addEventListener('pointermove', (e) => {
    if (!eqHold) return;
    const [x, y] = pos(e);
    if (eqHold.id === 'lowcut') {
      const f = Math.pow(10, Math.log10(20) + ((x - 30) / (eqGeo.w - 40)) * 3);
      sendFat('lowcut', 'freq', Math.round(Math.max(40, Math.min(400, f))));
    } else if (eqHold.id === 'mid' || eqHold.id === 'pres') {
      const f = Math.pow(10, Math.log10(20) + ((x - 30) / (eqGeo.w - 40)) * 3), [lo, hi, st] = eqHold.id === 'mid' ? [200, 1000, 10] : [2000, 6000, 50];
      sendFat('eq', eqHold.id + '_f', Math.round(Math.max(lo, Math.min(hi, f)) / st) * st);
      sendFat('eq', eqHold.id, Math.max(-6, Math.min(6, Math.round(((eqGeo.h / 2 - y) / (eqGeo.h / 2 - 14)) * 12 * 2) / 2)));
    } else {
      const gdb = ((eqGeo.h / 2 - y) / (eqGeo.h / 2 - 14)) * 12 * (eqHold.half ? 2 : 1);
      sendFat('eq', eqHold.id, Math.max(-6, Math.min(6, Math.round(gdb * 2) / 2)));
    }
    drawFatEq(); fatRender();
  });
  c.addEventListener('pointerup', () => { eqHold = null; });
  // the wheel over Mid or Presence: its Q (up narrower), about 10% a notch
  c.addEventListener('wheel', (e) => {
    const [x, y] = pos(e), p = near(x, y);
    if (!p || (p.id !== 'mid' && p.id !== 'pres')) return;
    e.preventDefault();
    const k = p.id + '_q', cur = F().eq[k] ?? (p.id === 'mid' ? 1.4 : 1);
    sendFat('eq', k, Math.max(0.5, Math.min(4, Math.round(cur * (e.deltaY < 0 ? 1.1 : 1 / 1.1) * 20) / 20)));
    drawFatEq(); fatRender();
  }, { passive: false });
  new ResizeObserver(() => drawFatEq()).observe(c);
}

function ioBuild() {
  $('inputs').innerHTML = INPUTS.map((c) => '<div class="inp"><div class="top"><b>' + c.name + '</b><span class="spacer"></span>' + (c.ch < 2 ? '<span class="note" style="margin:0">' + t('dsp') + '</span><button class="sw" role="switch" id="dsp_' + c.key + '"></button>' : '') + '</div>' +
    lvl('gain_' + c.key, t('gain'), c.lo, c.hi, 0.5) + lvl('pan_' + c.key, t('pan'), -1, 1, 0.05) +
    (c.ch < 2 ? sw('rec_' + c.key, t('rec'), ' ' + t('rec_small')) : '') +
    (c.ch === 0 ? sw('p48', t('phantom'), ' ' + t('phantom_small')) : '') +
    '</div>').join('');
  fatBuild();
  for (const c of INPUTS) {
    wireRange('gain_' + c.key, (v) => sendSet('gain', c.key, v), (v) => v.toFixed(1) + ' dB');
    wireRange('pan_' + c.key, (v) => sendSet('pan', c.key, v), fmtPan, { pan: true });
    if (c.ch < 2) $('dsp_' + c.key).onclick = () => sendSet('dsp', c.key, !setting('dsp', c.key));  // Line In has no DSP
    if (c.ch < 2) $('rec_' + c.key).onclick = () => sendSet('record_processed', c.key, !setting('record_processed', c.key));
    // 48V: asked first every time it goes on (a ribbon or tube mic can be damaged)
    if (c.ch === 0) $('p48').onclick = () => { const on = !setting('phantom'); if (!on || confirm(t('phantom_confirm'))) sendSet('phantom', '', on); };
  }
  $('outputs').innerHTML = lvl('mainVol', t('main_vol'), 0, 100, 1) + lvl('blend', t('blend'), -1, 1, 0.02) + lvl('phVol', t('phones_vol'), 0, 100, 1) + sw('phMute', t('phones_mute')) +
    BUSES.map((b) => sw('mono_' + b.id, t('mono'), ' ' + t(b.key))).join('');
  wireRange('mainVol', (v) => sendSet('main-volume', '', v), (v) => Math.round(v) + '%');
  wireRange('blend', (v) => sendSet('blend', '', v), fmtBlend, false);
  $('blend').parentElement.title = t('blend_tip');
  wireRange('phVol', (v) => sendSet('phones-volume', '', v), (v) => Math.round(v) + '%');
  $('phMute').onclick = () => sendSet('phones-mute', '', !setting('phones-mute'));
  const bk = { 0: 'main', 1: 'stream-a', 2: 'stream-b' };
  for (const b of BUSES) $('mono_' + b.id).onclick = () => sendSet('mono', bk[b.id], !setting('mono', bk[b.id]));
  // styles (settings.REVERB_STYLES, after TC-Helicon R1's) and an amount (the mics' send; the middle is the style's
  // own level), the reverb's own settings under Advanced. No on/off: its on word changes nothing (recorded 2026-11-09)
  $('reverb').innerHTML = '<div class="seg" id="rvFam" style="margin-top:4px">' + RV_FAMILIES.map(([f]) => '<button data-f="' + f + '">' + t('fam_' + f) + '</button>').join('') + '</div>' +
    '<div class="seg steps rvstyles" id="rvStyle"></div>' +
    lvl('rvAmt', t('rv_amount'), 0, 100, 1) + '<p class="note" id="rvNote"></p>' +
    '<details class="rvadv"><summary>' + t('rv_adv') + '</summary>' +
    lvl('rvMix', t('rv_mix'), 0, 100, 1) + lvl('rvPre', t('rv_pre'), 0, 200, 1) + lvl('rvSize', t('rv_size'), 0, 100, 1) + lvl('rvHp', t('rv_hp'), 20, 1000, 5) + '</details>';
  $('rvFam').onclick = (e) => { const b = e.target.closest('button'); if (b) { rvFam = b.dataset.f; ioRender(); } };
  $('rvStyle').onclick = (e) => { const b = e.target.closest('button'); if (b) rvSet({ style: b.dataset.v }); };
  wireRange('rvAmt', (v) => sendSet('reverb', '', { amount: v / 100 }), (v) => (v <= 0 ? t('off') : Math.round(v) + '%'));
  $('rvAmt').addEventListener('change', () => rvSet({}));
  const rv = (k, scale) => (v) => sendSet('reverb', '', { [k]: v * scale });
  wireRange('rvMix', rv('mix', 0.01), (v) => Math.round(v) + '%');
  wireRange('rvPre', rv('predelay', 0.001), (v) => Math.round(v) + ' ms', { unit: 'ms' });
  wireRange('rvSize', rv('size', 0.01), (v) => Math.round(v) + '%');
  wireRange('rvHp', rv('hp', 1), (v) => Math.round(v) + ' Hz');
}
// the reverb's styles (settings.REVERB_STYLES) in their families: ours, and two made from published presets ("y"
// Yamaha SPX2000's, "d" Dragonfly Reverb's; the page names the families only)
const RV_FAMILIES = [['ours', ['ambience', 'room', 'studio', 'club', 'plate', 'hall', 'theatre', 'arena']],
  ['y', ['y-vocal-plate', 'y-vocal-plate-x', 'y-vocal', 'y-vocal-chamber', 'y-presence', 'y-small-room', 'y-medium-hall', 'y-echo-room']],
  ['d', ['d-large-vocal-room', 'd-vocal-studio', 'd-small-vocal-hall', 'd-medium-vocal-hall', 'd-large-vocal-hall', 'd-clear-plate']]];
const RV_STYLES = RV_FAMILIES.flatMap(([, l]) => l);
const RV_LABEL = { 'y-vocal-plate': 'Vocal Plate', 'y-vocal-plate-x': 'Vocal Plate X', 'y-vocal': 'Vocal', 'y-vocal-chamber': 'Vocal Chamber', 'y-presence': 'Presence',
  'y-small-room': 'Small Room', 'y-medium-hall': 'Medium Hall', 'y-echo-room': 'Echo Room', 'd-large-vocal-room': 'Large Vocal Room', 'd-vocal-studio': 'Vocal Studio',
  'd-small-vocal-hall': 'Small Vocal Hall', 'd-medium-vocal-hall': 'Medium Vocal Hall', 'd-large-vocal-hall': 'Large Vocal Hall', 'd-clear-plate': 'Clear Plate' };
const rvName = (k) => RV_LABEL[k] || t('rv_' + k);
const rvFamOf = (k) => (RV_FAMILIES.find(([, l]) => l.includes(k)) || [null])[0];
let rvFam = null;
// a style or the amount let go: the state again (the reverb's return may have been put into the mixes)
async function rvSet(v) {
  try { if (Object.keys(v).length) await api('/api/set', { what: 'reverb', key: '', value: v }); S = await api('/api/state'); banner(''); } catch (e) { banner(t('send_fail') + e.message); }
  render();
}
function ioRender() {
  for (const c of INPUTS) {
    showRange('gain_' + c.key, DEV ? DEV.gain[c.ch] : undefined, (v) => (+v).toFixed(1) + ' dB');
    showRange('pan_' + c.key, setting('pan', c.key), fmtPan);
    if (c.ch < 2) showSw('dsp_' + c.key, setting('dsp', c.key));
    if (c.ch < 2) showSw('rec_' + c.key, setting('record_processed', c.key));
    if (c.ch === 0) showSw('p48', setting('phantom'));
  }
  showRange('mainVol', DEV ? DEV.main * 100 : undefined, (v) => Math.round(v) + '%');
  showRange('blend', setting('blend'), fmtBlend);
  showRange('phVol', setting('phones-volume'), (v) => Math.round(v) + '%');
  showSw('phMute', setting('phones-mute'));
  const bk = { 0: 'main', 1: 'stream-a', 2: 'stream-b' };
  for (const b of BUSES) showSw('mono_' + b.id, setting('mono', bk[b.id]));
  const r = setting('reverb');
  const fam = rvFam || rvFamOf(r && r.style) || 'ours';
  for (const b of $('rvFam').children) b.setAttribute('aria-pressed', String(b.dataset.f === fam));
  if ($('rvStyle').dataset.k !== fam + LANG) { $('rvStyle').dataset.k = fam + LANG; $('rvStyle').innerHTML = RV_FAMILIES.find(([f]) => f === fam)[1].map((k) => '<button data-v="' + k + '">' + rvName(k) + '</button>').join(''); }
  for (const b of $('rvStyle').children) b.setAttribute('aria-pressed', String(!!r && r.style === b.dataset.v));
  showRange('rvAmt', r && r.amount !== undefined ? r.amount * 100 : undefined, (v) => (v <= 0 ? t('off') : Math.round(v) + '%'));
  $('rvNote').textContent = r && r.style === 'custom' ? t('rv_custom') : t(fam === 'ours' ? 'rv_note' : 'rv_note_pub');
  showRange('rvMix', r ? r.mix * 100 : undefined, (v) => Math.round(v) + '%');
  showRange('rvPre', r ? r.predelay * 1000 : undefined, (v) => Math.round(v) + ' ms');
  showRange('rvSize', r ? r.size * 100 : undefined, (v) => Math.round(v) + '%');
  showRange('rvHp', r ? r.hp : undefined, (v) => Math.round(v) + ' Hz');
  fatRender();
  if (typeof consoleRender === 'function') consoleRender();
}

// ------------------------------------------------------------------ building the strips
const TICKS = [10, 0, -10, -20, -40, -60];
function faderHtml() {
  return '<div class="scale">' + TICKS.map((d) => '<span style="top:' + (8 + (1 - dbToPos(d)) * 244) + 'px">' + (d > 0 ? '+' : '') + d + '</span>').join('') + '</div>' +
    '<div class="fader" tabindex="0" role="slider" aria-valuemin="-60" aria-valuemax="10"><div class="track"></div><div class="fill"></div>' +
    TICKS.map((d) => '<div class="tick' + (d === 0 ? ' zero' : '') + '" style="top:' + (8 + (1 - dbToPos(d)) * 244) + 'px"></div>').join('') + '<div class="cap"></div></div>';
}
function meterHtml(n, guess) { return '<div class="meter' + (guess ? ' guess' : '') + '">' + '<i><b></b></i>'.repeat(n) + '</div>'; }

function build() {
  document.documentElement.lang = LANG === 'zh' ? 'zh-Hant' : 'en';
  for (const el of document.querySelectorAll('[data-i18n]')) el.textContent = t(el.dataset.i18n);
  for (const b of $('lang').children) { b.setAttribute('aria-pressed', b.dataset.v === LANG); b.onclick = () => { LANG = b.dataset.v; try { localStorage.setItem('io44.lang', LANG); } catch (e) { /* */ } build(); render(); }; }
  $('buses').innerHTML = BUSES.map((b) => '<button data-b="' + b.id + '">' + t(b.key) + '</button>').join('');
  for (const b of $('buses').children) b.onclick = () => { bus = +b.dataset.b; try { localStorage.setItem('io44.bus', bus); } catch (e) { /* */ } render(); };
  $('strips').innerHTML = SOURCES.map((s) => '<div class="strip" data-s="' + s.id + '"><div class="name">' + s.name + '</div><div class="kind">' + t(s.kind) + '</div>' +
    '<div class="body">' + faderHtml() + meterHtml(s.meter === 'mic1' || s.meter === 'mic2?' ? 1 : 2, s.meter.endsWith('?')) + '</div>' +
    '<div class="val"></div><button class="mute"></button></div>').join('');
  for (const el of $('strips').children) wire(el, +el.dataset.s);
  $('master').innerHTML = '<div class="name"></div><div class="kind">' + t('bus_out') + '</div><div class="body">' + meterHtml(2, false) + '</div><div class="val num"></div>';
  $('pwNames').innerHTML = PW.map(([k, n, m]) => '<li><b>' + n + '</b><span>' + t(k) + (m ? ' · ' + t(m) : '') + '</span></li>').join('');
  $('pwBtn').onclick = pipewire;
  ioBuild();
  if (typeof consoleBuild === 'function') consoleBuild();  // layout A (console.js)
  if (typeof scopeBuild === 'function') scopeBuild();      // layout B (scope.js)
  $('rates').innerHTML = [['auto', t('rate_auto')], [44100, '44.1 kHz'], [48000, '48 kHz'], [88200, '88.2 kHz'], [96000, '96 kHz']].map(([v, l]) => '<button data-v="' + v + '">' + l + '</button>').join('');
  for (const b of $('rates').children) b.onclick = () => rate(b.dataset.v, b.textContent);
}

function wire(el, src) {
  const f = el.querySelector('.fader');
  let drag = null;
  const set = (d, now) => { d = roundDb(Math.max(-145, Math.min(10, d))); show(el, src, d); send(src, d); };
  const fromY = (y) => { const r = f.getBoundingClientRect(); return 1 - (y - r.top - 8) / (r.height - 16); };
  f.addEventListener('pointerdown', (e) => {
    f.setPointerCapture(e.pointerId); f.focus();
    const cur = value(src);
    const capY = f.getBoundingClientRect().top + 8 + (1 - dbToPos(cur ?? 0)) * (f.getBoundingClientRect().height - 16);
    // grabbing the cap moves it relative to where it was; clicking the track jumps there
    drag = cur !== null && Math.abs(e.clientY - capY) < 12 ? { y: e.clientY, p: dbToPos(cur) } : null;
    if (!drag) { set(posToDb(fromY(e.clientY))); drag = { y: e.clientY, p: fromY(e.clientY) }; }
  });
  f.addEventListener('pointermove', (e) => {
    if (!drag) return;
    const r = f.getBoundingClientRect(), k = e.shiftKey ? 0.25 : 1;
    set(posToDb(Math.max(0, Math.min(1, drag.p + (drag.y - e.clientY) * k / (r.height - 16)))));
  });
  f.addEventListener('pointerup', () => { drag = null; });
  f.addEventListener('dblclick', () => set(0));
  if (typeof numEdit === 'function') numEdit(el.querySelector('.val'), { lo: -60, hi: 10, step: 0.5, get: () => value(src), apply: (d) => set(d) });
  f.addEventListener('wheel', (e) => { e.preventDefault(); const cur = value(src) ?? 0; set((cur <= -100 ? -60 : cur) - Math.sign(e.deltaY) * (e.shiftKey ? 0.5 : 1)); }, { passive: false });
  f.addEventListener('keydown', (e) => {
    const d = { ArrowUp: 1, ArrowRight: 1, ArrowDown: -1, ArrowLeft: -1 }[e.key];
    if (d) { e.preventDefault(); const cur = value(src) ?? 0; set((cur <= -100 ? -60 : cur) + d * (e.shiftKey ? 0.5 : 1)); }
  });
  // mute: off, and back to the value before (kept in this browser), 0 dB when there was none
  el.querySelector('.mute').onclick = () => {
    const cur = value(src), key = 'io44.before.' + bus + '.' + src;
    if (cur !== null && cur <= -100) { let b = 0; try { b = +(localStorage.getItem(key) ?? 0); } catch (e) { /* */ } set(b); }
    else { try { if (cur !== null) localStorage.setItem(key, cur); } catch (e) { /* */ } set(-145); }
  };
}

function show(el, src, d) {
  const f = el.querySelector('.fader'), known = d !== null, p = dbToPos(known ? d : 0);
  f.classList.toggle('unknown', !known);
  f.querySelector('.cap').style.top = 8 + (1 - p) * 244 + 'px';
  f.querySelector('.fill').style.height = (known ? p * 244 : 0) + 'px';
  f.setAttribute('aria-valuenow', known ? d : '');
  const v = el.querySelector('.val');
  if (v.dataset.editing !== '1') { v.textContent = known ? fmtDb(d) : t('unknown'); v.classList.toggle('unknown', !known); }
  const off = known && d <= -100;
  el.classList.toggle('off', off);
  const m = el.querySelector('.mute');
  m.setAttribute('aria-pressed', off);
  m.textContent = off ? t('muted') : t('mute');
}

function render() {
  for (const b of $('buses').children) b.setAttribute('aria-pressed', +b.dataset.b === bus);
  const B = BUSES.find((b) => b.id === bus);
  $('busNote').textContent = t(B.note);
  for (const el of $('strips').children) show(el, +el.dataset.s, value(+el.dataset.s));
  $('master').querySelector('.name').textContent = t(B.key);
  $('pwState').textContent = S.pipewire ? t('pw_on') : t('pw_offstate');
  $('pwState').className = 'chip' + (S.pipewire ? ' ok' : '');
  $('pwBtn').textContent = S.pipewire ? t('pw_remove') : t('pw_install');
  const R = S.rate || {};
  for (const b of $('rates').children) b.setAttribute('aria-pressed', String(R.set ?? 'auto') === b.dataset.v);
  $('rateNow').textContent = t('rate_running') + ' ' + (R.now === 'idle' || !R.now ? t('rate_idle') : R.now);
  ioRender();
  conn();
}

function conn(ok = S.connected, knob = null) {
  $('conn').textContent = ok ? t('connected') : t('offline');
  $('conn').className = 'chip ' + (ok ? 'ok' : 'off');
  if (knob !== null) $('knob').textContent = t('main_knob') + ' ' + Math.round(knob * 100) + '%';
  $('knob').hidden = knob === null && !$('knob').textContent;
}

function banner(msg) { $('banner').textContent = msg; $('banner').hidden = !msg; }

// ------------------------------------------------------------------ meters, about 12 times a second
const pos = (d) => 1 - Math.pow(Math.min(60, Math.max(0, -d)) / 60, 0.7);
function setBars(meterEl, vals) {
  const bars = meterEl.querySelectorAll('b');
  bars.forEach((b, i) => { b.style.height = pos(vals[Math.min(i, vals.length - 1)]) * 100 + '%'; });
}
async function tick() {
  try {
    const r = await api('/api/meters');
    S.connected = r.ok;
    if (r.ok) {
      const m = r.meters;
      for (const el of $('strips').children) { const s = SOURCES.find((x) => x.id === +el.dataset.s); setBars(el.querySelector('.meter'), m[s.meter] || [-150]); }
      const out = m[BUSES.find((b) => b.id === bus).meter];
      setBars($('master').querySelector('.meter'), out);
      $('master').querySelector('.val').textContent = Math.max(...out).toFixed(0) + ' dB';
      DEV = m.device; ioRender();
      if (typeof scopePush === 'function') { scopePush(m); if (document.body.dataset.layout === 'b') matrixMeters(m); }
      conn(true, m['main-knob']);
    } else conn(false);
  } catch (e) { conn(false); }
  setTimeout(tick, 80);
}

async function pipewire() {
  const install = !S.pipewire;
  if (!confirm(install ? t('pw_confirm_install') : t('pw_confirm_remove'))) return;
  $('pwBtn').disabled = true; $('pwMsg').textContent = t('pw_working');
  try { const r = await api('/api/pipewire', { install }); S.pipewire = r.pipewire; $('pwMsg').textContent = r.message; }
  catch (e) { $('pwMsg').textContent = e.message; }
  $('pwBtn').disabled = false; render();
}

async function rate(v, label) {
  const cur = String((S.rate || {}).set ?? 'auto');
  if (v === cur || !confirm(t(S.platform === 'win32' ? 'rate_confirm_win' : 'rate_confirm').replace('{r}', label))) return;
  for (const b of $('rates').children) b.disabled = true;
  $('rateNow').textContent = t('pw_working');
  try { const r = await api('/api/rate', { rate: v === 'auto' ? 'auto' : +v }); S.rate = r.rate; } catch (e) { banner(e.message); }
  for (const b of $('rates').children) b.disabled = false;
  render();
}

// started once every script is in (console.js comes after this one)
addEventListener('DOMContentLoaded', async function start() {
  build();
  try { S = await api('/api/state'); } catch (e) { banner(e.message); }
  render();
  // PipeWire's names and the sample-rate rule are Linux's: not on Windows
  if (S.platform === 'win32') {
    $('pwPart').hidden = true;
    $('rateNote').textContent = t('rate_note_win');
    $('rates').querySelector('[data-v="auto"]').hidden = true;  // no system rate to follow there
  }
  // #fat, or #fat-comp (a part picked): a link straight to the Fat Channel
  if (location.hash.startsWith('#fat')) { const p = location.hash.split('-')[1]; if (secsOf('mic1').includes(p)) { FPICK = p; fatDetailBuild(); fatRender(); } if (!/noscroll/.test(location.search)) $('fatCard').scrollIntoView(); }
  tick();
});
