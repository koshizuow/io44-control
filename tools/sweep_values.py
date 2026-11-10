#!/usr/bin/env python3
"""sweep_values.py HOST OUT.jsonl : set chosen parameters of the io44 to several values each through Universal
Control's service (ucctl.UC), holding each for SETTLE s, so a USB capture taken meanwhile shows how a setting turns
into what the device gets (where one step per parameter, as sweep.py does, is not enough to see the formula). Every
parameter is put back to its value at the start, and the whole state is compared at the end.

The list is for the parts still not worked out on 2026-11-09: the mic compressor, the gate's switch and key listen,
the EQ band types, the voice effects. The mics are not heard in the speakers while Main's monitor blend is 1 (all
playback); the echo's feedback stays at or under 0.6. 48V is never touched."""
import json
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from ucctl import UC, flat  # noqa: E402

SETTLE = 2.0
STEPS = [
    ("line/ch1/comp/input", [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]),
    ("line/ch1/comp/output", [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]),
    ("line/ch1/comp/ratio", [i / 10 for i in range(11)]),
    ("line/ch1/comp/attack", [0.0, 0.25, 0.5, 0.75, 1.0]),
    ("line/ch1/comp/release", [0.0, 0.25, 0.5, 0.75, 1.0]),
    ("line/ch1/comp/on", [0.0]),
    ("line/ch1/comp/keylisten", [1.0]),
    ("line/ch1/gate/on", [1.0]),
    ("line/ch1/gate/keylisten", [1.0]),
    ("line/ch2/eq/eqtype4", [0.0, 1 / 3, 2 / 3, 1.0]),
    ("line/ch2/eq/eqtype1", [0.0, 1 / 3, 2 / 3, 1.0]),
    ("line/ch1/voicefx/on", [1.0]),  # left on for the four below, put back after them
    ("line/ch1/voicefx/time", [0.0, 0.25, 0.5, 0.75, 1.0]),
    ("line/ch1/voicefx/feedback", [0.0, 0.2, 0.4, 0.6]),
    ("line/ch1/voicefx/mix", [0.0, 0.5, 1.0]),
    ("line/ch1/voicefxopt/fxmodel", [0.0, 0.25, 0.5, 0.75, 1.0]),
]
HOLD_UNTIL = {"line/ch1/voicefx/on": "line/ch1/voicefxopt/fxmodel"}

# a plain sequence of (name, value), everything put back at the end: the mic compressor's output at ratio steps 2 and
# 4, its input at step 3 (the ratio knob: step = round(value * 4))
# the voice effects (Mic 1 only): each model (fxmodel 0, 0.2, .. 0.8; 1.0 the echo, done) on, each of its knobs
# through five values (2026-11-09: the models' knobs as Universal Control lists them)
FX_MODELS = {0.0: ["lows", "width", "mix"], 0.2: ["detune", "mix"],
             0.4: ["avol", "acarriertype", "acarrierfreq", "avoiced", "mix"],
             0.6: ["bcarrierfreq", "bcarrier2", "bcarrier2freq", "bdist", "bvol", "mix"],
             0.8: ["ctune", "cfb", "cdamp", "cdist", "cvol", "mix"]}


# the compressor and EQ models other than the mics' own (2026-11-09): opt/compmodel 0 Standard, 0.5 Tube (1 FET is
# the input/output one, done); opt/eqmodel 0.5 Passive, 1 Vintage (0 Standard, the four bands, done). Choosing a model
# resets its knobs; each is switched on, then every knob through five values and back to the middle.
MODELS = [("line/ch1/opt/compmodel", 0.0, "line/ch1/comp/on",
           ["threshold", "ratio", "attack", "release", "gain", "softknee", "kneewidth", "automode"], "comp"),
          ("line/ch1/opt/compmodel", 0.5, "line/ch1/comp/on", ["gain", "peak", "mode"], "comp")]
# (the EQ's Passive and Vintage models were swept too on 2026-11-09, then left out: PreSonus's own designs, not used)


def modes_sequence():
    """what the first models sweep left open: the Tube's limit mode across peak, the Standard's auto mode with the
    attack and release turned, the knee width with the soft knee on"""
    p, s = "line/ch1/comp/", "line/ch1/opt/compmodel"
    seq = [(s, 0.5), (p + "on", 1.0), (p + "mode", 1.0)]
    seq += [(p + "peak", x) for x in (0.0, 0.25, 0.5, 0.75, 1.0)] + [(p + "gain", x) for x in (0.0, 1.0, 0.5)]
    seq += [(p + "mode", 0.0), (s, 0.0), (p + "on", 1.0), (p + "softknee", 1.0)]
    seq += [(p + "kneewidth", x) for x in (0.0, 0.5, 1.0)]
    seq += [(p + "automode", 1.0)] + [(p + "attack", x) for x in (0.0, 1.0)] + [(p + "release", x) for x in (0.0, 1.0)]
    seq += [(p + "automode", 0.0)]
    return seq


def startup_sequence():
    """which Universal Control values send the start-up words not identified yet (Appl Pari 7, 11, 13, 15, 16, 19,
    Para 14): each candidate to another value and back (autogain left alone: it moves the gain by itself)"""
    seq = []
    for n, vals, back in (("global/outputDelay", (0.5, 1.0), 0.0), ("global/outputDelayBus", (0.5, 1.0), 0.0),
                          ("global/phonesSrc", (0.5, 1.0), 0.0), ("global/enableChannelAssign", (1.0,), 0.0),
                          ("line/ch1/dawpostdsp", (0.0,), 1.0), ("line/ch1/stereopan", (0.0,), 1.0),
                          ("line/ch1/autogainmode", (0.5, 1.0), 0.0), ("line/ch1/hardwareMute", (1.0,), 0.0),
                          ("line/ch2/dawpostdsp", (0.0,), 1.0), ("line/ch1/activePresetSlotIndex", (1.0,), 0.0)):
        seq += [(n, v) for v in vals] + [(n, back)]
    return seq


def models_sequence():
    seq = []
    for model, v, on, knobs, sec in MODELS:
        seq += [(model, v), (on, 1.0)]
        for k in knobs:
            seq += [(f"line/ch1/{sec}/{k}", x) for x in (0.0, 0.25, 0.5, 0.75, 1.0)] + [(f"line/ch1/{sec}/{k}", 0.5)]
    return seq


def fx_sequence():
    seq = []
    for m, knobs in FX_MODELS.items():
        seq += [("line/ch1/voicefxopt/fxmodel", m), ("line/ch1/voicefx/on", 1.0)]
        for k in knobs:
            seq += [(f"line/ch1/voicefx/{k}", v) for v in (0.0, 0.25, 0.5, 0.75, 1.0)] + [(f"line/ch1/voicefx/{k}", 0.5)]
        seq.append(("line/ch1/voicefx/on", 0.0))
    return seq


SEQUENCES = {
    "comp2": [("line/ch1/comp/ratio", 0.5)] + [("line/ch1/comp/output", v) for v in (0.0, 0.25, 0.5, 0.75, 1.0)]
    + [("line/ch1/comp/output", 0.7321428656578064), ("line/ch1/comp/ratio", 1.0)]
    + [("line/ch1/comp/output", v) for v in (0.0, 0.25, 0.5, 0.75, 1.0)]
    + [("line/ch1/comp/output", 0.7321428656578064), ("line/ch1/comp/ratio", 0.75)]
    + [("line/ch1/comp/input", v) for v in (0.0, 0.25, 0.5, 0.75, 1.0)],
}


def main():
    host, out = sys.argv[1], sys.argv[2]
    named = {"fx": fx_sequence, "models": models_sequence, "modes": modes_sequence, "startup": startup_sequence}
    seq = (named[sys.argv[3]]() if sys.argv[3] in named else SEQUENCES[sys.argv[3]]) if len(sys.argv) > 3 else None
    uc = UC(host)
    before = dict(flat(uc.wait_state()))
    if before.get("global/monitorBlend") != 1.0:
        raise SystemExit("Main's monitor blend is not 1: the mics would be in the speakers; not sweeping")
    log = open(out, "w")
    log.write(json.dumps({"t": time.time(), "step": "start"}) + "\n")
    held = {}
    for n, v in seq or []:
        uc.set(n, float(v))
        log.write(json.dumps({"t": time.time(), "name": n, "step": "set", "value": v}) + "\n")
        log.flush()
        uc.pump(SETTLE)
    for n, vals in ([] if seq else STEPS):
        if n not in before:
            raise SystemExit(f"{n}: no such value")
        for v in vals:
            uc.set(n, float(v))
            log.write(json.dumps({"t": time.time(), "name": n, "step": "set", "value": v}) + "\n")
            log.flush()
            uc.pump(SETTLE)
        if n in HOLD_UNTIL:
            held[HOLD_UNTIL[n]] = n
            continue
        for m in [n] + ([held.pop(n)] if n in held else []):
            uc.set(m, float(before[m]))
            log.write(json.dumps({"t": time.time(), "name": m, "step": "back", "value": before[m]}) + "\n")
            log.flush()
            uc.pump(SETTLE)
        print(n, "done", flush=True)
    uc.close()
    uc = UC(host)
    after = dict(flat(uc.wait_state()))
    diff = [(n, before[n], after.get(n)) for n in before if before[n] != after.get(n)]
    for n, a, b in diff:
        if isinstance(a, (int, float)) and "48v" not in n:
            uc.set(n, float(a))
    uc.pump(1.0)
    uc.close()
    log.write(json.dumps({"t": time.time(), "step": "end", "diff": diff}) + "\n")
    print("differences after the sweep (put back):", diff)


if __name__ == "__main__":
    main()
