"""io44-control's own settings, and the messages they turn into.

The io44 does not report its settings (only the gains, Main's volume and the monitor blend), so this computer keeps
them and writes all of them whenever the io44 is there. They are io44-control's own: a neutral start, the gains, Main
and the blend read from the io44, and every change made from here. Nothing is taken from Universal Control: its
files, presets and its ways of turning knobs into filters were only looked at to learn what each message means
(the protocol: docs in README, tools/ for how it was found).

The processing is stream-mic's design (/stream-mic, crates/dsp): a low cut and three EQ bands (RBJ biquads, the same
responses as its Simper SVFs), a compressor with its knobs, a gate, a limiter. The io44 runs them; the parts it has
are fixed: per mic a high-pass (filt, Bqdf band 1), four EQ biquads (eq, bands 0-3), a gate (gate), a compressor
(comp, cpxt) and a limiter (lim); Mic 1 also a voice effect (target 201). Every filter is also sent for the four
rates in an MBdf message.

What the messages' fields mean (USB captures and recordings, 2026-11-08/09):
  cpxt: 5 key-filter words, attack s, release s, 1 - 1/ratio, half the knee width dB, threshold dBFS (the input's
    RMS), make-up gain (linear), on, key listen (recorded: a threshold -40 ratio 10 curve within 0.3 dB, the knee as
    threshold +- the field, quadratic)
  gate: 5 key-filter words, the range and the threshold as gains (10^(range/20), 10^(-threshold/20)), attack s,
    release s, the attack's and the release's per-sample coefficients, then hold (samples), on, expander, key listen
  lim : on, 10^(-threshold/20), the release's per-sample coefficient
  vrvb: on (changes nothing: recorded), mix (wet/dry: 0 returns the dry send), 1, predelay s, size, the high-pass Hz
    and its biquad
  target 0 per input: Para 1 the reverb send dB, Para 2 the pan (0..1), Pari 3 what the computer records from a mic
    and the stream mixes get (1 after the Fat Channel, 0 before)
  Appl per input: Para 3 the gain, Para 4 the processing (1 on, 0 bypassed), Pari 12 the processing channel, 9 link,
    7 a hardware mute, 15 (unknown, 0), 19 stereo pan off; global: Para 10 the monitor blend (the device keeps it, it
    does not apply it: Main is written again), Pari 13 the output delay (-1 off) with Para 14, Pari 11 its bus
  mixes (bus 100, mprm): pairs of a source and a gain in dB; Pari 8 mono
"""
import math
import struct

from . import proto

FS = 48000.0
RATES = (44100.0, 48000.0, 88200.0, 96000.0)
OFF_DB = -145.0
PASS = (1.0, 0.0, 0.0, 0.0, 0.0)
INPUTS = ("mic1", "headset", "line")  # channels 0, 1, 2
MICS = ("mic1", "headset")
# mix sources: 0 Playback, 1 Virtual A, 2 Virtual B, 3 Mic 1, 4 Headset, 5 the reverb's return, 6 Line In
SOURCES = {0: "playback", 1: "virtual-a", 2: "virtual-b", 3: "mic1", 4: "headset", 5: "fx", 6: "line"}
BUS_KEYS = {0: "main", 1: "stream-a", 2: "stream-b"}
VERSION = 2


# ---- filters ---------------------------------------------------------------------------------------------------------

def _norm(b0, b1, b2, a0, a1, a2):
    # the device's order: b0, -a1, b1, -a2, b2
    return (b0 / a0, -a1 / a0, b1 / a0, -a2 / a0, b2 / a0)


def rbj(kind: str, f: float, gain_db: float = 0.0, q: float = 0.7071, fs: float = FS) -> tuple:
    """the RBJ cookbook biquads (the same responses as stream-mic's Simper SVFs with the cookbook Q)"""
    a = 10 ** (gain_db / 40)
    w = 2 * math.pi * min(f, 0.49 * fs) / fs
    c, s = math.cos(w), math.sin(w)
    al = s / (2 * q)
    if kind == "peak":
        return _norm(1 + al * a, -2 * c, 1 - al * a, 1 + al / a, -2 * c, 1 - al / a)
    if kind in ("lowshelf", "highshelf"):
        sg = 1 if kind == "lowshelf" else -1
        sq = 2 * math.sqrt(a) * al
        return _norm(a * ((a + 1) - sg * (a - 1) * c + sq), sg * 2 * a * ((a - 1) - sg * (a + 1) * c),
                     a * ((a + 1) - sg * (a - 1) * c - sq), (a + 1) + sg * (a - 1) * c + sq,
                     -sg * 2 * ((a - 1) + sg * (a + 1) * c), (a + 1) + sg * (a - 1) * c - sq)
    if kind == "highpass":
        return _norm((1 + c) / 2, -(1 + c), (1 + c) / 2, 1 + al, -2 * c, 1 - al)
    if kind == "lowpass":
        return _norm((1 - c) / 2, 1 - c, (1 - c) / 2, 1 + al, -2 * c, 1 - al)
    if kind == "bandpass":
        return _norm(al, 0.0, -al, 1 + al, -2 * c, 1 - al)
    raise ValueError(kind)


def stable(co: tuple) -> bool:
    """a biquad in the device's order is safe to send: finite, its poles inside the unit circle"""
    if not all(math.isfinite(x) for x in co):
        return False
    a1, a2 = -co[1], -co[3]
    return abs(a2) < 1 and abs(a1) < 1 + a2


def lin(db: float) -> float:
    return 10 ** (db / 20)


def db(x: float) -> float:
    return 20 * math.log10(x) if x > 0 else OFF_DB


def coef(seconds: float, fs: float = FS) -> float:
    """a one-pole smoothing coefficient for a time constant (stream-mic's definition)"""
    return math.exp(-1.0 / (max(seconds, 1e-5) * fs))


def _f(*v) -> bytes:
    return struct.pack(f"<{len(v)}f", *v)


def multi_rate(band: int, design) -> bytes:
    """MBdf: the filter for each of the four rates, the count 4 last"""
    words = struct.pack("<I", band)
    for fs in RATES:
        co = design(fs)
        if not stable(co):
            raise ValueError(f"filter band {band} unstable at {fs:g} Hz")
        words += _f(*co, fs)
    return words.ljust(484, b"\0") + struct.pack("<I", 4)


def biquad(band: int, design) -> bytes:
    co = design(FS)
    if not stable(co):
        raise ValueError(f"filter band {band} unstable")
    return struct.pack("<I", band) + _f(*co)


# ---- the knobs: (key, low, high) for a number, (key, None) for a switch ------------------------------------------------
# stream-mic's ranges where it has the part (crates/dsp, ui/app.js), the times in ms

FAT_KEYS = {
    "lowcut": {"on": None, "freq": (40.0, 400.0)},
    "eq": {"on": None, "low": (-6.0, 6.0), "pres": (-6.0, 6.0), "air": (-6.0, 6.0)},
    "gate": {"on": None, "expander": None, "threshold": (-80.0, -20.0), "range": (3.0, 80.0), "attack": (0.1, 50.0),
             "hold": (1.0, 300.0), "release": (40.0, 2000.0)},
    "comp": {"on": None, "threshold": (-40.0, -6.0), "ratio": (1.0, 8.0), "knee": (0.0, 12.0), "attack": (1.0, 40.0),
             "release": (30.0, 400.0), "makeup": (0.0, 18.0)},
    "limit": {"on": None, "ceiling": (-12.0, 0.0), "release": (20.0, 200.0)},
}
EQ_BANDS = (("lowshelf", 200.0, 0.7071, "low"), ("peak", 3000.0, 1.0, "pres"), ("highshelf", 10000.0, 0.7071, "air"))


def fat_defaults() -> dict:
    """a mic's processing, all off (stream-mic's talk values ready for when a part is switched on)"""
    return {"lowcut": {"on": 0, "freq": 80.0},
            "eq": {"on": 0, "low": 0.0, "pres": 1.5, "air": 1.0},
            "gate": {"on": 0, "expander": 1, "threshold": -54.0, "range": 12.0, "attack": 3.0, "hold": 80.0,
                     "release": 200.0},
            "comp": {"on": 0, "threshold": -24.0, "ratio": 3.0, "knee": 6.0, "attack": 10.0, "release": 120.0,
                     "makeup": 6.0},
            "limit": {"on": 0, "ceiling": -1.0, "release": 50.0}}


def fat_value(section: str, key: str, value):
    """a value checked for its key: a number in range, a switch as 0/1; ValueError otherwise"""
    keys = FAT_KEYS.get(section, {})
    if key not in keys:
        raise ValueError(f"no such setting: {section} {key}")
    if keys[key] is None:
        return int(bool(value))
    v = float(value)
    lo, hi = keys[key]
    if not math.isfinite(v) or not lo <= v <= hi:
        raise ValueError(f"{section} {key}: {lo:g}..{hi:g}")
    return v


def lowcut_design(ch: dict):
    lc = ch["lowcut"]
    return (lambda fs: rbj("highpass", lc["freq"], q=0.7071, fs=fs)) if lc["on"] else (lambda fs: PASS)


def eq_designs(ch: dict) -> list:
    """the four EQ biquads: low shelf 200 Hz, presence bell 3 kHz Q 1, air shelf 10 kHz, the fourth flat"""
    e = ch["eq"]
    out = []
    for kind, f, q, key in EQ_BANDS:
        g = float(e[key]) if e["on"] else 0.0
        out.append((lambda fs, kind=kind, f=f, q=q, g=g: rbj(kind, f, g, q, fs)) if g else (lambda fs: PASS))
    out.append(lambda fs: PASS)
    return out


# The times on the page are time constants, as in stream-mic. What the io44 makes of its fields was measured with Main
# Out L wired into Input 1 (2026-11-09, 1 kHz steps of 12 dB, the gain's path in 0.25 ms steps):
#   compressor: the attack field is about 2.5 time constants (0.01..0.1 s: 2.1-2.7), the release field about 4.6
#     (the time to 99%: 0.1..2 s, 63% reached after field / 4.6, a short pause first included)
#   limiter: the release coefficient's time constant comes out 0.57 times as long (0.02..0.5 s), after a 25 ms pause
#   gate: only the two coefficients count (the seconds fields change nothing); closing comes out about 4.7 times
#     slower than the coefficient's time constant (30..300 ms; never faster than about 35 ms), opening about 3 times;
#     a hold of 0 keeps it shut for good, so it is at least 1 ms
COMP_ATTACK, COMP_RELEASE, LIMIT_RELEASE, GATE_ATTACK, GATE_RELEASE = 2.5, 4.6, 1 / 0.57, 1 / 3, 1 / 4.7


def gate_fields(ch: dict) -> bytes:
    g = ch["gate"]
    att, rel = g["attack"] / 1000, g["release"] / 1000
    return (_f(*PASS, lin(-g["range"]), lin(-g["threshold"]), att, rel, coef(att * GATE_ATTACK), coef(rel * GATE_RELEASE))
            + struct.pack("<4I", max(48, round(g["hold"] / 1000 * FS)), int(g["on"]), int(g["expander"]), 0))


def comp_fields(ch: dict) -> bytes:
    c = ch["comp"]
    return (_f(*PASS, c["attack"] / 1000 * COMP_ATTACK, c["release"] / 1000 * COMP_RELEASE, 1 - 1 / max(1.0, c["ratio"]),
               max(0.01, c["knee"] / 2), c["threshold"], lin(c["makeup"])) + struct.pack("<2I", int(c["on"]), 0))


def limit_fields(ch: dict) -> bytes:
    lm = ch["limit"]
    return struct.pack("<Iff", int(lm["on"]), lin(-lm["ceiling"]), coef(lm["release"] / 1000 * LIMIT_RELEASE))


# ---- the whole state ---------------------------------------------------------------------------------------------------

def default_state(gains: dict = None, blend: float = 1.0) -> dict:
    """a neutral start: every input into every mix at 0 dB (Main through the monitor blend), playback and the virtual
    outputs in Main only, nothing sent to the reverb, no processing; the gains as the io44 has them"""
    gains = gains or {}

    def inp(key):
        d = {"gain": float(gains.get(key, 0.0)), "pan": 0.0, "fx": OFF_DB, "main": 0.0, "stream-a": 0.0,
             "stream-b": 0.0}
        if key in MICS:
            d.update(dsp=True, record_processed=True, **fat_defaults())
        return d
    return {"v": VERSION,
            "inputs": {k: inp(k) for k in INPUTS},
            "returns": dict({k: {"main": 0.0, "stream-a": OFF_DB, "stream-b": OFF_DB}
                             for k in ("playback", "virtual-a", "virtual-b")},
                            fx={"main": 0.0, "stream-a": 0.0, "stream-b": 0.0}),
            "mono": {b: False for b in BUS_KEYS.values()},
            "reverb": reverb_style("hall", amount=0.0),
            "voicefx": voice_default(5, on=0),
            "blend": blend}


def blend_gains(blend: float) -> tuple:
    """the monitor blend p (-1 inputs only .. 0 both .. +1 playback only) as the inputs' and the playback's gains in
    Main, dB (a plain crossfade, each side full until the middle)"""
    p = max(-1.0, min(1.0, blend))
    return db(min(1.0, 1.0 - p)), db(min(1.0, 1.0 + p))


def source_gain(st: dict, src: int, bus: int) -> float:
    """what one source is sent to one bus at, dB: Main through the blend (inputs and the reverb's return on the input
    side, so the stream mixes keep their reverb whatever the blend)"""
    name, b = SOURCES[src], BUS_KEYS[bus]
    strip = st["inputs"][name] if name in st["inputs"] else st["returns"][name]
    g = float(strip[b])
    if bus == 0:
        inp, play = blend_gains(st["blend"])
        g += inp if name in st["inputs"] or name == "fx" else play
    return max(OFF_DB, g)


def mixes(st: dict) -> dict:
    return {bus: [(s, source_gain(st, s, bus)) for s in SOURCES] for bus in BUS_KEYS}


def set_mix(st: dict, bus: int, src: int, g: float):
    """a mix value set from the page or the command line (dB as sent), into the state (Main's net of the blend)"""
    name, b = SOURCES[src], BUS_KEYS[bus]
    strip = st["inputs"][name] if name in st["inputs"] else st["returns"][name]
    if bus == 0:
        inp, play = blend_gains(st["blend"])
        term = inp if name in st["inputs"] or name == "fx" else play
        g = g if g <= OFF_DB or term <= OFF_DB else g - term
    strip[b] = g


def fat_writes(st: dict, ci: int, section: str = None) -> list:
    """one mic's processing (or one part of it): (target, index, kind, data, channel)"""
    ch = st["inputs"][INPUTS[ci]]
    c = proto.code
    out = []
    if section in (None, "lowcut"):
        d = lowcut_design(ch)
        # (the high-pass is band 1 in its Bqdf but 0 in its MBdf)
        out += [(c("filt"), ci, "MBdf", multi_rate(0, d), 0), (c("filt"), ci, "Bqdf", biquad(1, d), 0)]
    if section in (None, "eq"):
        for band, d in enumerate(eq_designs(ch)):
            out += [(c("eq  "), ci, "MBdf", multi_rate(band, d), 0), (c("eq  "), ci, "Bqdf", biquad(band, d), 0)]
    if section in (None, "gate"):
        out += [(c("gate"), ci, "MBdf", multi_rate(0, lambda fs: PASS), 0), (c("gate"), ci, "gate", gate_fields(ch), 0)]
    if section in (None, "comp"):
        out += [(c("comp"), ci, "MBdf", multi_rate(0, lambda fs: PASS), 0), (c("comp"), ci, "cpxt", comp_fields(ch), 0)]
    if section in (None, "limit"):
        out.append((c("lim "), ci, "lim ", limit_fields(ch), 0))
    return out


# ---- the reverb: styles and an amount -------------------------------------------------------------------------------
# The io44's reverb measured through a loopback (2026-11-09; captures/reverb_20261109): it starts 24 ms after the dry
# by itself, sparse for its first 20 ms; size sets the decay steeply and darkens it (1 kHz: 0 0.66 s, 0.1 0.73,
# 0.2 0.86, 0.3 0.96, 0.4 1.10, 0.5 1.27, 0.6 1.50, 0.7 1.86, 0.8 2.54, 0.9 3.77, 1 7.2 s); the low cut is a 12 dB/oct
# high-pass and the pre-delay adds to the 24 ms. The styles follow TC-Helicon VoiceTone R1's (its manual's table:
# length, tone, initial reflections, pre-delay) as far as these three allow (the reflections and a bright tail are
# not the io44's to change); the vocal ranges from mixing guides (lead 0.8-2 s; pre-delay room 5-20, plate 15-35,
# hall 20-60 ms). (size, pre-delay s, low cut Hz, the send at the amount's middle, dB: worked out from the measured
# responses for a wet level 11-17 dB under the dry, set by one A/B recording; to be checked by ear)
REVERB_STYLES = {
    "ambience": (0.0, 0.0, 400.0, -15.3), "room": (0.1, 0.0, 300.0, -14.3), "studio": (0.2, 0.0, 200.0, -14.5),
    "club": (0.3, 0.010, 200.0, -13.2), "plate": (0.5, 0.025, 350.0, -12.8), "hall": (0.55, 0.035, 180.0, -12.4),
    "theatre": (0.6, 0.030, 120.0, -13.4), "arena": (0.8, 0.070, 150.0, -12.5)}
REVERB_KEYS = {"mix": (0.0, 1.0), "predelay": (0.0, 0.5), "size": (0.0, 1.0), "hp": (20.0, 1000.0), "amount": (0.0, 1.0)}


def reverb_style(name: str, amount: float = 0.5) -> dict:
    size, pre, hp, _ = REVERB_STYLES[name]
    return {"style": name, "amount": amount, "mix": 1.0, "predelay": pre, "size": size, "hp": hp}


def reverb_send(st: dict) -> float:
    """the mics' send to the reverb, dB: the style's own level at the amount's middle (0.5), +-9 dB at its ends
    (0 off); a custom setting is levelled as the nearest style by size"""
    r = st["reverb"]
    a = float(r.get("amount", 0.0))
    if a <= 0:
        return OFF_DB
    style = r.get("style")
    if style not in REVERB_STYLES:
        style = min(REVERB_STYLES, key=lambda k: abs(REVERB_STYLES[k][0] - float(r["size"])))
    return REVERB_STYLES[style][3] + 30 * math.log10(a / 0.5)


def reverb_set(st: dict, key: str, value):
    """a style (its settings, the amount kept), the amount, or one of the reverb's own settings (the style becomes
    "custom")"""
    r = st["reverb"]
    if key == "style":
        if value not in REVERB_STYLES:
            raise ValueError("reverb style: " + ", ".join(REVERB_STYLES))
        st["reverb"] = reverb_style(value, amount=float(r.get("amount", 0.5)))
    elif key in REVERB_KEYS:
        v = float(value)
        lo, hi = REVERB_KEYS[key]
        if not math.isfinite(v) or not lo <= v <= hi:
            raise ValueError(f"reverb {key}: {lo:g}..{hi:g}")
        r[key] = v
        if key != "amount":
            r["style"] = "custom"
    else:
        raise ValueError(f"reverb: no {key}")
    # a reverb sent with nowhere to come back: its return into every mix at 0 dB (Main under the blend's input side)
    if r.get("amount", 0) > 0 and all(float(g) <= OFF_DB for g in st["returns"]["fx"].values()):
        st["returns"]["fx"] = {"main": 0.0, "stream-a": 0.0, "stream-b": 0.0}
    return st["reverb"]


def reverb_write(st: dict):
    r = st["reverb"]
    hp = min(1000.0, max(20.0, float(r["hp"])))
    co = rbj("highpass", hp, q=0.7071)
    return (202, 0, "vrvb", struct.pack("<IfIfff5f", 1, min(1.0, max(0.0, r["mix"])), 1, min(0.5, max(0.0, r["predelay"])),
                                         min(1.0, max(0.0, r["size"])), hp, *co), 0)


def writes(st: dict) -> list:
    """everything, written whenever the io44 is there (it starts on its own defaults after being unplugged). 48V is
    never written: it stays as the device has it."""
    A = proto.code("Appl")
    out = []
    for ci, k in enumerate(INPUTS):
        ch = st["inputs"][k]
        send = reverb_send(st) if k in MICS and "amount" in st["reverb"] else float(ch["fx"])
        out.append((0, 0, "Para", struct.pack("<If", 1, max(OFF_DB, send)), ci))
        out.append((A, 0, "Para", struct.pack("<If", 3, float(ch["gain"])), ci))
        if k in MICS:
            out += fat_writes(st, ci)
    out += voice_writes(st)
    out.append(reverb_write(st))
    for bus, gains in sorted(mixes(st).items()):
        out.append(("mprm", bus, gains))
    out.append((A, 0, "Para", struct.pack("<If", 10, float(st["blend"])), 0))
    for ci, k in enumerate(INPUTS):
        ch = st["inputs"][k]
        if k in MICS:
            out.append((A, 0, "Para", struct.pack("<If", 4, 1.0 if ch["dsp"] else 0.0), ci))
            out.append((A, 0, "Pari", struct.pack("<II", 12, ci), ci))
            out.append((A, 0, "Pari", struct.pack("<II", 9, 0), ci))
            out.append((0, 0, "Pari", struct.pack("<II", 3, int(bool(ch["record_processed"]))), ci))
            out.append((A, 0, "Pari", struct.pack("<II", 19, 0), ci))
            out.append((A, 0, "Pari", struct.pack("<II", 7, 0), ci))
        out.append((A, 0, "Pari", struct.pack("<II", 15, 0), ci))
        out.append((0, 0, "Para", struct.pack("<If", 2, (float(ch["pan"]) + 1) / 2), ci))
    for bus, b in BUS_KEYS.items():
        out.append((100, bus, "Pari", struct.pack("<II", 8, int(bool(st["mono"][b]))), 0))
    # no output delay
    out += [(A, 0, "Pari", struct.pack("<II", 11, 0), 0), (A, 0, "Para", struct.pack("<If", 14, 0.0), 0),
            (A, 0, "Pari", struct.pack("<Ii", 13, -1), 0)]
    return out


def blend_writes(st: dict) -> list:
    """after the blend moved: Main's mix again"""
    return [("mprm", 0, mixes(st)[0])]


def view(st: dict) -> dict:
    """what the page shows: the mixes as sent, the settings, the mics' processing"""
    return {"mix": {str(b): {str(s): round(g, 2) for s, g in gains} for b, gains in mixes(st).items()},
            "set": {"dsp": {k: bool(st["inputs"][k]["dsp"]) for k in MICS},
                    "record_processed": {k: bool(st["inputs"][k]["record_processed"]) for k in MICS},
                    "pan": {k: st["inputs"][k]["pan"] for k in INPUTS},
                    "mono": dict(st["mono"]), "reverb": dict(st["reverb"]), "blend": st["blend"],
                    **{k: st[k] for k in ("phones-volume", "phones-mute", "phantom") if k in st}},
            "fat": {k: dict({s: dict(st["inputs"][k][s]) for s in FAT_KEYS},
                            **({"voicefx": dict(st["voicefx"])} if k == "mic1" else {})) for k in MICS}}


# ---- Mic 1's voice effect (target 201) ---------------------------------------------------------------------------------
# What the io44 has (USB captures 2026-11-09): VoFx picks the effect, then its own message; choosing one makes the io44
# set it up for a moment and drop what comes meanwhile (Io44.write_all sends the effect's messages again after a
# second). The filters some need are ours (their places in the io44 as found: Detune band 0; Doubler bands 0 and 1;
# Robot A 22 bands, 0-9 high-passes and 10-19 low-passes making ten band-passes, 20 a low-pass, 21 a high-pass, and
# the same 22 at the current rate in an inia block).
#   0 Doubler  godv: on, low boost (0..1), width, low boost, mix
#   1 Detune   may4: on, -semitones (a signed integer, 0..-8), 0, 0, 0, mix
#   2 Robot A  bota: on, carrier (0 noise, 1 saw, 2 square), carrier Hz, volume, 1, 1, mix
#   3 Robot B  botb: on, carrier Hz, distortion, volume, second carrier on, its Hz, mix
#   4 Robot C  botc: on, tune Hz (an integer), feedback, damping, distortion, volume, mix
#   5 Echo     vech: on, mix, feedback, time s
VOICE_NAMES = {0: "Doubler", 1: "Detune", 2: "Robot A", 3: "Robot B", 4: "Robot C", 5: "Echo"}
VOICE_KEYS = {
    0: {"low": (0.0, 1.0), "width": (0.0, 1.0), "mix": (0.0, 1.0)},
    1: {"semitones": "0-8", "mix": (0.0, 1.0)},
    2: {"carrier": "0-2", "freq": (50.0, 500.0), "volume": (0.0, 1.0), "mix": (0.0, 1.0)},
    3: {"freq": (0.1, 2000.0), "distortion": (0.0, 1.0), "volume": (0.0, 1.0), "freq2_on": None,
        "freq2": (0.1, 2000.0), "mix": (0.0, 1.0)},
    4: {"tune": (250.0, 1550.0), "feedback": (0.5, 0.85), "damping": (0.3, 0.9), "distortion": (0.0, 1.0),
        "volume": (0.0, 1.0), "mix": (0.0, 1.0)},
    5: {"time": (0.01, 0.25), "feedback": (0.0, 0.45), "mix": (0.0, 1.0)},
}
VOICE_START = {0: {"low": 0.3, "width": 0.6, "mix": 0.5}, 1: {"semitones": 3, "mix": 0.6},
               2: {"carrier": 1, "freq": 110.0, "volume": 1.0, "mix": 0.7},
               3: {"freq": 60.0, "distortion": 0.2, "volume": 1.0, "freq2_on": 0, "freq2": 5.0, "mix": 0.7},
               4: {"tune": 700.0, "feedback": 0.7, "damping": 0.6, "distortion": 0.2, "volume": 1.0, "mix": 0.6},
               5: {"time": 0.18, "feedback": 0.25, "mix": 0.4}}
# our filters: Doubler's low boost (a shelf at 250 Hz, up to +9 dB, the second at 180 Hz), Detune's low-pass (7 kHz),
# Robot A's ten channels (100 Hz .. 7 kHz, each a high-pass at the channel's bottom and a low-pass a third of an octave
# above its top, Q 1.5) with a low-pass at 400 Hz and a high-pass at 3 kHz
DOUBLER_SHELVES = ((250.0, 9.0), (180.0, 6.0))
DETUNE_LP = 7000.0
ROBOT_A = {"lo": 100.0, "hi": 7000.0, "q": 1.5, "lp": 400.0, "hp": 3000.0}


def voice_default(model: int, on: int = 0) -> dict:
    return dict(VOICE_START[model], model=model, on=on)


def voice_set(st: dict, key: str, value):
    """one voice-effect setting: "model" chooses the effect (its knobs start at our values), "on", or a knob"""
    fx = st["voicefx"]
    if key == "model":
        m = int(value)
        if m not in VOICE_KEYS:
            raise ValueError("voice effect: 0-5")
        st["voicefx"] = voice_default(m, on=int(fx.get("on", 0)))
        return m
    if key == "on":
        fx["on"] = int(bool(value))
        return fx["on"]
    rule = VOICE_KEYS[fx["model"]].get(key, "none")
    if rule == "none":
        raise ValueError(f"voice effect {VOICE_NAMES[fx['model']]} has no {key}")
    v = float(value)
    if not math.isfinite(v):
        raise ValueError(f"{key}: not a number")
    if rule is None:
        v = int(bool(v))
    elif isinstance(rule, str):
        hi = int(rule.split("-")[1])
        if v != int(v) or not 0 <= v <= hi:
            raise ValueError(f"{key}: an integer 0..{hi}")
        v = int(v)
    elif not rule[0] <= v <= rule[1]:
        raise ValueError(f"{key}: {rule[0]:g}..{rule[1]:g}")
    fx[key] = v
    return v


def robot_a_designs() -> list:
    """Robot A's 22 filters (as design(fs)): ten channels' high-passes, their low-passes, a low-pass, a high-pass"""
    r = ROBOT_A
    edges = [r["lo"] * (r["hi"] / r["lo"]) ** (i / 10) for i in range(11)]
    hps = [lambda fs, f=edges[i]: rbj("highpass", f, q=r["q"], fs=fs) for i in range(10)]
    lps = [lambda fs, f=edges[i + 1] * 2 ** (1 / 3): rbj("lowpass", min(f, 18000.0), q=r["q"], fs=fs) for i in range(10)]
    return hps + lps + [lambda fs: rbj("lowpass", r["lp"], q=0.7071, fs=fs), lambda fs: rbj("highpass", r["hp"], q=0.7071, fs=fs)]


def voice_writes(st: dict) -> list:
    """Mic 1's voice effect: VoFx, its filters, its message"""
    fx = st["voicefx"]
    m = int(fx["model"])
    T = 201
    on = int(fx.get("on", 0))
    g = lambda k: float(fx[k])
    out = [(T, 0, "VoFx", struct.pack("<I", m), 0)]
    if m == 0:
        for band, (f, top) in enumerate(DOUBLER_SHELVES):
            d = lambda fs, f=f, gain=top * g("low"): rbj("lowshelf", f, gain, 0.7071, fs)
            out += [(T, 0, "MBdf", multi_rate(band, d), 0), (T, 0, "Bqdf", biquad(band, d), 0)]
        out.append((T, 0, "godv", struct.pack("<Iffff", on, g("low"), g("width"), g("low"), g("mix")), 0))
    elif m == 1:
        d = lambda fs: rbj("lowpass", DETUNE_LP, q=0.7071, fs=fs)
        out += [(T, 0, "MBdf", multi_rate(0, d), 0), (T, 0, "Bqdf", biquad(0, d), 0)]
        out.append((T, 0, "may4", struct.pack("<IiIIIf", on, -int(fx["semitones"]), 0, 0, 0, g("mix")), 0))
    elif m == 2:
        ds = robot_a_designs()
        out += [(T, 0, "MBdf", multi_rate(band, d), 0) for band, d in enumerate(ds)]
        out.append((T, 0, "inia", b"".join(_f(*d(FS)) for d in ds), 0))
        out.append((T, 0, "bota", struct.pack("<IIffIIf", on, int(fx["carrier"]), g("freq"), g("volume"), 1, 1, g("mix")), 0))
    elif m == 3:
        out.append((T, 0, "botb", struct.pack("<IfffIff", on, g("freq"), g("distortion"), g("volume"), int(fx["freq2_on"]),
                                              g("freq2"), g("mix")), 0))
    elif m == 4:
        out.append((T, 0, "botc", struct.pack("<IIfffff", on, int(round(g("tune"))), g("feedback"), g("damping"),
                                              g("distortion"), g("volume"), g("mix")), 0))
    else:
        out.append((T, 0, "vech", struct.pack("<Ifff", on, g("mix"), g("feedback"), g("time")), 0))
    return out
