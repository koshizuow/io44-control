#!/usr/bin/env python3
"""usbparse.py CAP.pcap [--all] : the non-isochronous transfers in a USBPcap capture (link type 249): time,
direction, endpoint, type, the setup packet of control transfers, and the data in hex (and as text where printable)"""
import struct
import sys

TYPES = {0: "ISO", 1: "INT", 2: "CTRL", 3: "BULK"}


def records(path):
    f = open(path, "rb").read()
    lt = struct.unpack("<I", f[20:24])[0]
    assert lt == 249, f"link type {lt}"
    i = 24
    while i + 16 <= len(f):
        ts, us, incl, orig = struct.unpack("<IIII", f[i:i + 16])
        p = f[i + 16:i + 16 + incl]
        i += 16 + incl
        hl, irp, status, func, info, bus, dev, ep, tt, dlen = struct.unpack("<HQIHBHHBBI", p[:27])
        rest = p[27:hl]
        data = p[hl:]
        yield dict(t=ts + us / 1e6, irp=irp, status=status, func=func, out=not (info & 1), bus=bus, dev=dev,
                   ep=ep, type=TYPES.get(tt, tt), stage=rest[0] if rest else None, data=data)


def text(b):
    return "".join(chr(c) if 32 <= c < 127 else "." for c in b)


if __name__ == "__main__":
    t0 = None
    for r in records(sys.argv[1]):
        if r["type"] == "ISO" and "--all" not in sys.argv:
            continue
        t0 = t0 or r["t"]
        d = r["data"]
        what = ""
        if r["type"] == "CTRL" and r["stage"] == 0 and len(d) >= 8:
            bm, req, val, idx, ln = struct.unpack("<BBHHH", d[:8])
            what = f"SETUP bm={bm:02x} req={req:02x} val={val:04x} idx={idx:04x} len={ln}"
            d = d[8:]
        elif r["type"] == "CTRL":
            what = {1: "DATA", 2: "STATUS", 3: "COMPLETE"}.get(r["stage"], str(r["stage"]))
        print(f"{r['t'] - t0:8.3f} {'host>dev' if r['out'] else 'dev>host'} ep={r['ep']:02x} {r['type']:4} {what} "
              f"[{len(d)}] {d[:96].hex()} {text(d[:96])}")
