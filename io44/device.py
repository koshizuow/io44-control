"""The io44 in names: its mixes, its meters. Everything here was checked on the device from Linux (2026-11-09) unless
marked otherwise.

Mixes (buses). Each bus is a list of (source, gain dB); -145 dB is off (the value Universal Control sends), -96 is
what it sends for "down" on the reverb return. A message may carry one source only: the others stay as they are, so
a change needs no knowledge of the rest of the bus.

How Universal Control knows the settings (USB capture of its service starting, 2026-11-09): it reads the Fat
Channel documents from the io44 (GetP MemP: the four preset keys' settings and the 28 stored presets, read_doc), and
writes everything else from the copy its service keeps on the computer (gains, the three mixes, every Fat Channel
coefficient, the reverb). The mixes cannot be read back; gains and Main's volume come in the meter reply.

  bus 0 Main (speakers, headphones)   bus 1 Stream Mix A (capture 5-6)   bus 2 Stream Mix B (capture 7-8)

  source 0 Playback   1 Virtual A   2 Virtual B   3 Mic 1   4 Headset (input 2, the headset jack's mic; Universal Control's
         "Headset Mic"; digital silence with no headset)
         5 FX return (the reverb)   6 Line In

Universal Control's "monitor blend" is not a device setting: at full "playback" it writes Main with the inputs off
and the playback channels on, at 0 dB.
"""
import math
import struct
import time

from . import proto, ubj
from .usb import Device

BUSES = {"main": 0, "stream-a": 1, "stream-b": 2}
BUS_NAMES = {0: "Main", 1: "Stream Mix A", 2: "Stream Mix B"}
SOURCES = {"playback": 0, "virtual-a": 1, "virtual-b": 2, "mic1": 3, "mic2": 4, "headset": 4, "fx": 5, "line": 6}
SOURCE_NAMES = {0: "Playback", 1: "Virtual A", 2: "Virtual B", 3: "Mic 1", 4: "Headset", 5: "FX return", 6: "Line In"}
OFF = -145.0

# Meter slots (floats from byte 28 of the JaSt reply, linear). Checked: 0-5 (a tone on each output channel), 14-15
# (every output reaches Main), 16-19 (turning Mic 1 off in a stream mix), 46 (Main's knob, 0.12 = the knob where it
# was). The rest is a reading of levels at rest and marked "?".
METERS = {
    "playback": (0, 1), "virtual-a": (2, 3), "virtual-b": (4, 5),
    "mic1": (6,), "mic1-post?": (7,), "mic2?": (8,), "mic2-post?": (9,),
    "fx?": (10, 11), "line?": (12, 13),
    "main": (14, 15), "stream-a": (16, 17), "stream-b": (18, 19),
}
GAIN_SLOTS = (48, 49, 50)       # each input's gain in dB, as set (read back, checked for Mic 1 and Mic 2)
GAIN_REDUCTION = range(20, 38)   # 18 values at 1.0 when nothing is reduced (the Fat Channel's dynamics, which ones?)
MAIN_KNOB = 46                   # the Main output knob, 0..1


def finite(*vals):
    """every value a real number: a NaN sent to the io44 silences every mix until its DSP starts over (2026-11-09,
    Universal Control's NaN reverb coefficients), so nothing here sends one, and a bad value is refused rather than
    quietly clamped (min/max turn a NaN into the bound)"""
    for v in vals:
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError(f"not a number: {v!r}")


VOICE_TARGET = 201  # the voice effects' messages
VOFX_SETTLE = 1.0  # seconds after VoFx before the effect's messages are taken
FLOAT_KINDS = {"Para", "mprm", "vrvb", "Bqdf", "MBdf", "Lfdf", "MLff", "gate", "cpxt", "lim ", "godv", "bota", "botb", "botc", "vech"}  # not may4 (a negative integer)


def db(x: float) -> float:
    x = abs(x)
    return 20 * math.log10(x) if x > 1e-9 else -150.0


# The inputs: chunk channel 0, 1, 2. Gain is in dB (Universal Control's 0..1 control over these ranges: Mic 1
# 0.48 -> 28.8, Mic 2 0.1 -> 3, Line In trim 0.4 -> -2.4).
INPUTS = {"mic1": 0, "mic2": 1, "headset": 1, "line": 2}  # mic2 = the headset jack's mic
INPUT_NAMES = {0: "Mic 1", 1: "Headset", 2: "Line In"}
GAIN_RANGE = {0: (0.0, 60.0), 1: (0.0, 30.0), 2: (-12.0, 12.0)}
APPL = proto.code("Appl")
# Para numbers on Appl (from the sweep, aligned on a known message): 1 headphone volume 0..1, 2 Main volume 0..1 (the
# front knob), 3 input gain dB (per channel), 4 the input's DSP amount 0..1 (Universal Control's "bypass DSP" sends 0).
# On target 0 (per channel): 1 the send to the effect (reverb) in dB, -145 off (checked 2026-11-09: -10 lit the FX
# meters; Universal Control sends -145 while FXA is 0), 2 pan 0..1. Pari on Appl: 6 headphones mute. Pari on a bus
# (target 100, index = bus): 8 mono.
P_PHONES, P_MAIN, P_GAIN, P_DSP = 1, 2, 3, 4
REVERB = 202  # target of vrvb: on (u32), mix 0..1, 1 (u32, unknown), pre-delay s, size 0..1, high-pass Hz, then that
# high-pass as a biquad worked out on the computer: b0, -a1, b1, -a2, b2 (a0 = 1). Without the five the device keeps
# whatever was there; NaN there made every mix silent until the io44 was power-cycled (2026-11-09).


def hp_biquad(f: float, fs: float = 48000.0, q: float = 0.7071) -> tuple:
    """RBJ high-pass, as Universal Control sends it (175 Hz at 48 kHz: 0.98377, 1.96729, -1.96755, -0.96780, 0.98377)"""
    if not (fs > 0 and 0 < f < fs / 2):
        raise ValueError(f"high-pass {f} Hz at {fs} Hz")
    w = 2 * math.pi * f / fs
    c, a = math.cos(w), math.sin(w) / (2 * q)
    a0 = 1 + a
    b0 = (1 + c) / 2 / a0
    return b0, 2 * c / a0, -2 * b0, -(1 - a) / a0, b0


class Io44:
    def __init__(self):
        self.d = Device()
        self.seq = 0

    def close(self):
        self.d.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def _next(self) -> int:
        self.seq = (self.seq + 1) & 0xFFFF
        return self.seq

    def raw_meters(self) -> tuple:
        self.d.write(proto.get_meters(self._next()))
        m = self.d.read()
        n = (len(m) - 28) // 4
        return struct.unpack(f"<{n}f", m[28:28 + 4 * n])

    def meters(self) -> dict:
        """dB per named meter (pairs are left, right), plus the Main knob as 0..1"""
        v = self.raw_meters()
        out = {k: [round(db(v[i]), 1) for i in idx] for k, idx in METERS.items()}
        out["main-knob"] = round(v[MAIN_KNOB], 3)
        return out

    def _set(self, target: int, index: int, kind: str, data: bytes, ch: int = 0):
        if kind in FLOAT_KINDS:  # the last check: no NaN or infinity in any float word of the message
            for (u,) in struct.iter_unpack("<I", data[:len(data) // 4 * 4]):
                if (u >> 23) & 0xFF == 0xFF:
                    raise ValueError(f"{kind}: a NaN or infinite value, not sent")
        self.d.write(proto.message(self._next(), "SetP", target, index, kind, data, ch=ch))
        r = proto.parse(self.d.read())
        if not r["reply"]:
            raise IOError(f"no acknowledgement: {r}")

    def state(self) -> dict:
        """what the io44 reports of its settings (in the meter reply): each input's gain, Main's volume"""
        v = self.raw_meters()
        return {"gain": {ch: round(v[GAIN_SLOTS[ch]], 2) for ch in INPUT_NAMES}, "main": round(v[MAIN_KNOB], 3)}

    def set_gain(self, ch: int, db: float):
        finite(db)
        lo, hi = GAIN_RANGE[ch]
        if not lo <= db <= hi:
            raise ValueError(f"gain {db} dB: {INPUT_NAMES[ch]} takes {lo:g}..{hi:g}")
        self._set(APPL, 0, "Para", struct.pack("<If", P_GAIN, db), ch=ch)

    def set_dawpost(self, ch: int, post: bool):
        """what the computer records from a mic (its USB input): after the Fat Channel (True) or before it"""
        self._set(0, 0, "Pari", struct.pack("<II", 3, int(bool(post))), ch=ch)

    def set_dsp(self, ch: int, amount: float):
        """the input's processing (Fat Channel, voice effects): 1 on, 0 bypassed"""
        finite(amount)
        self._set(APPL, 0, "Para", struct.pack("<If", P_DSP, min(1.0, max(0.0, amount))), ch=ch)

    def set_pan(self, ch: int, pan: float):
        """0 left, 0.5 centre, 1 right"""
        finite(pan)
        self._set(0, 0, "Para", struct.pack("<If", 2, min(1.0, max(0.0, pan))), ch=ch)

    def set_main_volume(self, v: float):
        finite(v)
        self._set(APPL, 0, "Para", struct.pack("<If", P_MAIN, min(1.0, max(0.0, v))))

    def set_phones_volume(self, v: float):
        finite(v)
        self._set(APPL, 0, "Para", struct.pack("<If", P_PHONES, min(1.0, max(0.0, v))))

    def set_phantom(self, ch: int, on: bool):
        """48V phantom power on Mic 1 (Appl Pari 0 on channel 0; Universal Control sends it at start from its file).
        Ribbon and tube microphones can be damaged by it: nothing in this program turns it on by itself (apply never
        writes it); only an explicit request does."""
        if ch != 0:
            # input 2 is the headset jack (Universal Control's "Headset Mic"; its file has no 48V there)
            raise ValueError("48V is on Mic 1 (the XLR input) only")
        self._set(APPL, 0, "Pari", struct.pack("<II", 0, int(bool(on))), ch=ch)

    def set_phones_mute(self, on: bool):
        self._set(APPL, 0, "Pari", struct.pack("<II", 6, int(on)))

    def set_mono(self, bus: int, on: bool):
        self._set(0x64, bus, "Pari", struct.pack("<II", 8, int(on)))

    def set_reverb(self, on: bool, mix: float, predelay: float, size: float, hp: float, fs: float = 48000.0):
        finite(mix, predelay, size, hp, fs)
        hp = min(1000.0, max(20.0, hp))
        co = hp_biquad(hp, fs)
        if not all(math.isfinite(x) for x in co):
            raise ValueError(f"reverb high-pass {hp} Hz at {fs} Hz")
        self._set(REVERB, 0, "vrvb", struct.pack("<IfIfff5f", int(on), min(1.0, max(0.0, mix)), 1,
                                                 min(0.5, max(0.0, predelay)), min(1.0, max(0.0, size)), hp, *co))

    def read_doc(self, kind: str, slot: int, index: int = None) -> dict:
        """a MemP document, as Universal Control reads them when its service starts (USB capture 2026-11-09):
        GetP Appl MemP, the chunk length set to the reply's room (2028), then the document kind, slot and index.
          kind "Stat", slot 0..3: the four preset keys' Fat Channel settings (Mic 1: 0 and 1, Mic 2: 2 and 3)
          kind "PrsM", slot 0..27: the presets kept in the io44 (Universal Control asks with index 27 - slot)
        The reply: the same 16 bytes, then 3 zero bytes, the document's length (u16) twice, 2 zero bytes and the
        document (UBJSON)."""
        if index is None:
            index = slot if kind == "Stat" else 27 - slot
        m = struct.pack("<HBBIIIIII", 44, 1, 1, self._next(), proto.code("GetP"), APPL, 0, proto.code("MemP"), 2028)
        m += struct.pack("<III", proto.code(kind), slot, index) + b"\0" * 4
        self.d.write(m)
        # exactly the reply's size, as Universal Control reads it: 2048 bytes are four full 512-byte packets with no
        # short one after, so a larger read waits for more until it times out
        r = self.d.read(20 + 2028, timeout_ms=3000)
        if len(r) < 49 or r[20:24] != m[20:24]:
            raise IOError(f"MemP reply: {r[:48].hex()}")
        n = struct.unpack("<H", r[43:45])[0]
        return ubj.loads(r[49:49 + n])

    def write_all(self, writes: list) -> int:
        """every write, as settings.writes makes them; returns how many"""
        for w in writes:
            if w[0] == "mprm":
                self.set_mix(w[1], [(s, max(-145.0, min(10.0, g))) for s, g in w[2]])
            else:
                target, index, kind, data, ch = w
                self._set(target, index, kind, data, ch=ch)
        # a voice effect chosen (VoFx): the io44 sets it up for a moment and drops what comes meanwhile, so the
        # effect's own messages are sent again after a second (heard 2026-11-09: sent once right after VoFx, Detune
        # and Echo did nothing; sent again a second later, both worked)
        if any(w[0] == VOICE_TARGET and w[2] == "VoFx" for w in writes):
            time.sleep(VOFX_SETTLE)
            for target, index, kind, data, ch in [w for w in writes if w[0] == VOICE_TARGET and w[2] != "VoFx"]:
                self._set(target, index, kind, data, ch=ch)
        return len(writes)

    def blend(self) -> float | None:
        """Main's monitor blend as the device keeps it (meter slot 47, the front panel's blend: +1 playback only, 0 both,
        -1 inputs only; checked by turning it, 2026-11-09), None if out of range"""
        v = self.raw_meters()[47]
        return v if -1.0 <= v <= 1.0 else None

    def set_mix(self, bus: int, gains: list[tuple[int, float]]):
        """some sources of one bus: [(source, dB)], the rest of the bus unchanged"""
        for s, g in gains:
            finite(g)
            if s not in SOURCE_NAMES or not -145.0 <= g <= 10.0:
                raise ValueError(f"source {s} gain {g}")
        if bus not in BUS_NAMES:
            raise ValueError(f"bus {bus}")
        m = proto.mix(self._next(), bus, gains)
        for (_, u) in struct.iter_unpack("<II", m[32:32 + 8 * len(gains)]):  # the gain words, as in _set
            if (u >> 23) & 0xFF == 0xFF:
                raise ValueError("mprm: a NaN or infinite gain, not sent")
        self.d.write(m)
        r = proto.parse(self.d.read())
        if not r["reply"]:
            raise IOError(f"no acknowledgement: {r}")
