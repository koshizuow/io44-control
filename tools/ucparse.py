"""ucparse.py CAP.pcap [PORT] : the TCP payloads to and from PORT in a raw-IP pcap (loopcap.ps1), in order, as UC
messages where they look like one, else hex"""
import struct, sys, zlib, json
f = open(sys.argv[1], "rb").read()
port = int(sys.argv[2]) if len(sys.argv) > 2 else 49670
i = 24
flows = {}
while i + 16 <= len(f):
    ts, us, incl, orig = struct.unpack("<IIII", f[i:i + 16]); p = f[i + 16:i + 16 + incl]; i += 16 + incl
    ihl = (p[0] & 15) * 4
    sp, dp = struct.unpack(">HH", p[ihl:ihl + 4])
    seq = struct.unpack(">I", p[ihl + 4:ihl + 8])[0]
    off = (p[ihl + 12] >> 4) * 4
    data = p[ihl + off:]
    if not data:
        continue
    key = (sp, dp)
    d = "C>S" if dp == port else "S>C"
    fl = flows.setdefault(key, {"dir": d, "seen": set(), "buf": b"", "t": ts + us / 1e6})
    if seq in fl["seen"]:
        continue  # the raw socket sees each loopback packet twice
    fl["seen"].add(seq)
    fl["buf"] += data
    fl.setdefault("order", []).append((ts + us / 1e6, data))
for key, fl in flows.items():
    print("=== flow %s %s->%s bytes %d" % (fl["dir"], key[0], key[1], len(fl["buf"])))
    b = fl["buf"]; j = 0; n = 0
    while j < len(b) and n < int(sys.argv[3]) if len(sys.argv) > 3 else j < len(b):
        if b[j:j + 4] == b"UC\x00\x01":
            size = struct.unpack("<H", b[j + 4:j + 6])[0]
            body = b[j + 6:j + 6 + size]
            code = body[:2]
            pl = body[6:]
            txt = ""
            if code == b"JM":
                txt = pl[4:].decode("utf8", "replace")[:700]
            elif code == b"ZB":
                try:
                    txt = "zlib %d -> %d bytes: %s" % (len(pl), len(zlib.decompress(pl[4:])), zlib.decompress(pl[4:])[:300])
                except Exception as e:
                    txt = "ZB? %s %s" % (e, pl[:40].hex())
            else:
                txt = pl[:60].hex() + " " + pl[:60].decode("latin1", "replace").encode("ascii", "replace").decode()
            print("  %s cb=%s %s" % (code.decode("latin1"), body[2:6].hex(), txt))
            j += 6 + size; n += 1
        else:
            print("  raw", b[j:j + 64].hex()); break
