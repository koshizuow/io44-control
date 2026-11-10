#!/usr/bin/env python3
"""sweep_match.py CAP.pcap SWEEP.jsonl [OUT.json] : what each step of sweep.py sent over USB. The capture is the
Windows machine's clock and the log this one's: they are lined up on the first step (it must send something), then
each control message from the host (bulk endpoint 0x01, the meter polls GetP left out) goes to the last step before it.
Messages are decoded as the Revelator's: 4 bytes, a request number, a 4-character command stored backwards (SetP),
two words, a 4-character kind (mprm: the mixer, pairs of a source index and a gain in dB), the payload's length."""
import json
import struct
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from usbparse import records  # noqa: E402


def fourcc(b):
    return b[::-1].decode("latin1")


def decode(d):
    if len(d) < 32:
        return {"raw": d.hex()}
    cmd, kind, n = fourcc(d[8:12]), fourcc(d[20:24]), struct.unpack("<I", d[24:28])[0]
    body = d[32:32 + n] if n else d[32:]
    out = {"cmd": cmd, "kind": kind, "len": n, "w": struct.unpack("<II", d[12:20])}
    if kind == "mprm":
        # 60 slots of (source index, gain dB), then the number of slots used (at 512 in a 516-byte message)
        cnt = struct.unpack("<I", d[512:516])[0] if len(d) >= 516 else len(body) // 8
        out["pairs"] = [(struct.unpack("<I", body[o:o + 4])[0], round(struct.unpack("<f", body[o + 4:o + 8])[0], 3)) for o in range(0, 8 * min(cnt, 60), 8)]
    else:
        out["body"] = body.rstrip(b"\x00").hex()
    return out


def main():
    cap, log = sys.argv[1], sys.argv[2]
    steps = [json.loads(l) for l in open(log)]
    moves = [s for s in steps if s.get("step") in ("set", "back")]
    msgs = []
    for r in records(cap):
        d = r["data"]
        if r["type"] == "BULK" and r["out"] and r["ep"] == 0x01 and len(d) > 12 and d[8:12] != b"PteG":
            msgs.append((r["t"], d))
    if not msgs or not moves:
        sys.exit("nothing to match")
    off = msgs[0][0] - moves[0]["t"]
    # the first step is not always the first thing sent (2026-11-09: Universal Control just started was still sending
    # its whole state, the steps came out 13 late): the clock offset is searched instead, the one that puts most
    # messages within 0.6 s after a step (Universal Control answers a step at once)
    import bisect
    starts = [s["t"] for s in moves]
    def fit(o):
        n = 0
        for t, _ in msgs:
            lt = t - o
            k = bisect.bisect_right(starts, lt) - 1
            n += k >= 0 and lt - starts[k] < 0.6
        return n
    cands = [off + x / 50 for x in range(-3000, 3001)]
    off = max(cands, key=fit)
    print(f"clock offset {off:.2f} s, {fit(off)} of {len(msgs)} messages within 0.6 s of a step", file=sys.stderr)
    per = [[] for _ in moves]
    for t, d in msgs:
        lt = t - off + 0.05
        k = max((i for i, s in enumerate(moves) if s["t"] <= lt), default=0)
        per[k].append(decode(d))
    res = []
    for s, m in zip(moves, per):
        res.append({"name": s["name"], "step": s["step"], "value": s["value"], "usb": m})
        print(f"{s['name']:32} {s['step']:4} {s['value']!s:>10}  " + "; ".join(
            f"{x.get('cmd')}/{x.get('kind')} " + (" ".join(f"{i}:{g}" for i, g in x["pairs"]) if "pairs" in x else x.get("body", x.get("raw", ""))[:80])
            for x in m) or "  (nothing)")
    if len(sys.argv) > 3:
        json.dump(res, open(sys.argv[3], "w"), indent=1)


if __name__ == "__main__":
    main()
