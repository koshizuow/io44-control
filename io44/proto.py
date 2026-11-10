"""The io44's control messages (bulk, interface 5), as Universal Control's service sends them (USB captures, 2026-11-08).

Every message: a 20-byte header, then one chunk.
  0  u16 total length          2  u8 1, u8 direction (0x01 host to device, 0x81 reply)
  4  u32 sequence number       8  4-char code, stored reversed: GetP, SetP (reply: Rply)
  12 u32 target: 'Appl' (global), 'opt ', or 0x64 (100) for a bus or channel
  16 u32 index under the target (a bus, a channel)
  20 4-char chunk type, reversed: JaSt (meters), mprm (a bus's mix matrix), Para, Pari, Bqdf, ...
  24 u32 chunk length (from byte 20 to the end)
  28 u32 the channel the chunk is for (0 Mic 1, 1 Mic 2, 2 Line In), 0 where there is none
  32 the chunk's data
"""
import struct

APPL = 0x4170706C  # 'Appl' as stored (reversed bytes of "lppA")


def code(s: str) -> int:
    """a 4-char code as the device stores it (the characters in reverse order, read as a little-endian u32)"""
    return struct.unpack("<I", s.encode()[::-1])[0]


def message(seq: int, op: str, target: int, index: int, kind: str, data: bytes, total: int = 0, ch: int = 0) -> bytes:
    body = struct.pack("<III", code(kind), 12 + len(data), ch) + data
    m = struct.pack("<HBBIIII", 0, 1, 1, seq, code(op), target, index) + body
    if total:
        m = m.ljust(total, b"\0")
        m = m[:24] + struct.pack("<I", total - 20) + m[28:]
    return struct.pack("<H", len(m)) + m[2:]


def parse(m: bytes) -> dict:
    """a reply: the meters' GetP comes back whole (Rply); a SetP is acknowledged with 8 bytes, the length, 1, 0x81 and
    the sequence number's low byte (seen: seq 1002 acknowledged as 0xea)"""
    if len(m) == 8:
        _, _, direction, seq = struct.unpack("<HBBI", m)
        return dict(total=8, reply=direction == 0x81, seq=seq, op="Ack", target=0, index=0, kind="", data=b"")
    total, _, direction, seq, op, target, index, kind, length = struct.unpack("<HBBIIIIII", m[:28])
    rev = lambda v: struct.pack("<I", v)[::-1].decode("latin-1")
    return dict(total=total, reply=direction == 0x81, seq=seq, op=rev(op), target=target, index=index, kind=rev(kind),
                data=m[32:20 + length] if length else m[32:])


def get_meters(seq: int) -> bytes:
    return message(seq, "GetP", code("Appl"), 0, "JaSt", b"", total=240)


def mix(seq: int, bus: int, gains: list[tuple[int, float]]) -> bytes:
    """a bus's mix: (source number, gain dB) pairs, -145 = off; 60 slots, the count at byte 512"""
    assert len(gains) <= 60
    data = b"".join(struct.pack("<If", s, g) for s, g in gains).ljust(60 * 8, b"\0")
    m = bytearray(message(seq, "SetP", 0x64, bus, "mprm", data, total=516))
    struct.pack_into("<I", m, 512, len(gains))
    return bytes(m)
