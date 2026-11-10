#!/usr/bin/env python3
"""sweep.py HOST OUT.jsonl [NAME_FILTER] : change every numeric parameter of the interface once and put it back, one at a
time, through Universal Control's service (ucctl.UC), so a USB capture taken meanwhile (USBPcapCMD on the Windows
machine) shows what each one sends. Per parameter: set a nearby value, wait SETTLE s, set the old value, wait SETTLE s;
OUT.jsonl gets one line per step with the local time, so the capture's bursts can be lined up in order.

Left out: names (text values), read-only and live values (clip, hardwareMute, meters), the 48V phantom power (user
2026-11-08: a tube mic on input 1; never switched here), auto gain (it runs a measurement), presets and hot keys (a
load changes many values at once), diagnostics. Values go a step toward the middle (+0.1 below 0.5, -0.1 above), the
main output only down, so nothing gets louder in the speakers. At the end the whole state is read again and compared
with the one at the start."""
import json
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from ucctl import UC, flat  # noqa: E402

SETTLE = 2.0   # the service sends to the device up to 1.2 s after a change: at 1 s the messages could not be told apart
SKIP = ("48v", "autogain", "autogainmode", "clip", "hardwareMute", "chnum", "name", "username", "preset_name",
        "presetHotKey", "presetHotKeyTitle", "activePresetSlotIndex", "queryDebugMessages", "select")


def skip(name, v):
    leaf = name.split("/")[-1]
    # presets/* and cache/* load or store a preset (changing many values and the preset names, which cannot be put back
    # through PV: the first sweep left ch2 showing "Telephone" with Broadcast HS's values)
    return (not isinstance(v, (int, float)) or leaf in SKIP or leaf.startswith("presetSlotTitle")
            or name.startswith("diagnostics/") or "/presets/" in name or "/cache/" in name)


def target(name, v):
    if name == "global/mainOutVolume":
        return max(0.0, v - 0.05)
    return round(v + 0.1 if v < 0.5 else v - 0.1, 6)


def main():
    host, out = sys.argv[1], sys.argv[2]
    filt = sys.argv[3] if len(sys.argv) > 3 else ""
    uc = UC(host)
    before = dict(flat(uc.wait_state()))
    todo = [(n, v) for n, v in before.items() if not skip(n, v) and filt in n]
    print(f"{len(todo)} parameters, about {len(todo) * 2 * SETTLE / 60:.0f} min", flush=True)
    log = open(out, "w")
    log.write(json.dumps({"t": time.time(), "step": "start", "n": len(todo)}) + "\n")
    for i, (n, v) in enumerate(todo):
        new = target(n, v)
        for step, val in (("set", new), ("back", v)):
            uc.set(n, float(val))
            log.write(json.dumps({"t": time.time(), "i": i, "name": n, "step": step, "value": val}) + "\n")
            log.flush()
            uc.pump(SETTLE)
        if i % 25 == 0:
            print(f"{i}/{len(todo)} {n}", flush=True)
    uc.close()
    # the whole state again, fresh: anything not back as it was is listed (and put back)
    uc = UC(host)
    after = dict(flat(uc.wait_state()))
    diff = [(n, before[n], after.get(n)) for n in before if before[n] != after.get(n)]
    for n, a, b in diff:
        if isinstance(a, (int, float)):
            uc.set(n, float(a))
    uc.pump(1.0)
    uc.close()
    log.write(json.dumps({"t": time.time(), "step": "end", "diff": diff}) + "\n")
    print("differences after the sweep:", diff)


if __name__ == "__main__":
    main()
