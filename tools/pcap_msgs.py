"""The io44 control messages in a USBPcap capture (Windows, link type 249): the host's bulk OUT messages on endpoint
0x01, in order. Used to compare what this program would send with what Universal Control sent."""
import struct
import sys


def rev(v: int) -> str:
    return struct.pack("<I", v)[::-1].decode("latin-1")


def messages(path: str, ep: int = 0x01) -> list[bytes]:
    f = open(path, "rb").read()
    i, out = 24, []
    while i + 16 <= len(f):
        incl = struct.unpack("<I", f[i + 8:i + 12])[0]
        p = f[i + 16:i + 16 + incl]
        i += 16 + incl
        hl = struct.unpack("<H", p[:2])[0]
        if p[21] == ep and len(p) - hl >= 28:
            out.append(p[hl:])
    return out


def describe(d: bytes) -> dict:
    tot, _, dr, seq, op, tg, ix, kind, ln = struct.unpack("<HBBIIIIII", d[:28])
    ch = struct.unpack("<I", d[28:32])[0]
    return dict(op=rev(op), target=rev(tg) if tg > 0x1000000 else tg, index=ix, kind=rev(kind), ch=ch, data=d[32:20 + ln], raw=d)


if __name__ == "__main__":
    for d in messages(sys.argv[1]):
        m = describe(d)
        if m["op"] != "SetP":
            continue
        k = m["kind"]
        data = m["data"]
        if k in ("Para",):
            v = struct.unpack("<If", data[:8])
        elif k in ("Pari",):
            v = struct.unpack("<II", data[:8])
        elif k == "mprm":
            n = struct.unpack("<I", d[512:516])[0]
            v = [struct.unpack("<If", data[8 * j:8 * j + 8]) for j in range(n)]
        elif k == "MemP":
            v = data[:24].hex(" ")
        else:
            nf = len(data) // 4
            v = [round(x, 6) for x in struct.unpack(f"<{nf}f", data[:4 * nf])]
            ints = struct.unpack(f"<{nf}I", data[:4 * nf])
            v = [i if i < 0x10000 else x for i, x in zip(ints, v)]
        print(f"{str(m['target']):5} {m['index']} {k:5} ch{m['ch']} len {len(data):3}: {v}")
