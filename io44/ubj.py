"""UBJSON (Universal Binary JSON), the format of the io44's MemP documents (the channel states and the presets).
Big-endian numbers; object keys are a length and the text, without a type marker."""
import struct


def _int(b, i, t):
    n = {"i": (1, ">b"), "U": (1, ">B"), "I": (2, ">h"), "l": (4, ">i"), "L": (8, ">q")}[t]
    return struct.unpack(n[1], b[i:i + n[0]])[0], i + n[0]


def _length(b, i):
    t = chr(b[i])
    return _int(b, i + 1, t)


def _value(b, i):
    t = chr(b[i])
    i += 1
    if t in "iUIlL":
        return _int(b, i, t)
    if t == "d":
        return struct.unpack(">f", b[i:i + 4])[0], i + 4
    if t == "D":
        return struct.unpack(">d", b[i:i + 8])[0], i + 8
    if t == "S" or t == "H":
        n, i = _length(b, i)
        return b[i:i + n].decode("utf-8", "replace"), i + n
    if t == "C":
        return chr(b[i]), i + 1
    if t == "T":
        return True, i
    if t == "F":
        return False, i
    if t == "Z":
        return None, i
    if t == "{":
        o = {}
        while chr(b[i]) != "}":
            n, i = _length(b, i)
            k = b[i:i + n].decode("utf-8", "replace")
            o[k], i = _value(b, i + n)
        return o, i + 1
    if t == "[":
        a = []
        while chr(b[i]) != "]":
            v, i = _value(b, i)
            a.append(v)
        return a, i + 1
    raise ValueError(f"UBJSON type {t!r} at {i - 1}")


def loads(b: bytes):
    v, _ = _value(b, 0)
    return v


def _w(v) -> bytes:
    if v is None:
        return b"Z"
    if v is True:
        return b"T"
    if v is False:
        return b"F"
    if isinstance(v, int):
        for t, f, lo, hi in (("i", ">b", -128, 127), ("I", ">h", -32768, 32767), ("l", ">i", -2**31, 2**31 - 1)):
            if lo <= v <= hi:
                return t.encode() + struct.pack(f, v)
        return b"L" + struct.pack(">q", v)
    if isinstance(v, float):
        return b"d" + struct.pack(">f", v)
    if isinstance(v, str):
        s = v.encode()
        return b"S" + _w(len(s)) + s
    if isinstance(v, dict):
        out = b"{"
        for k, x in v.items():
            kb = k.encode()
            out += _w(len(kb)) + kb + _w(x)
        return out + b"}"
    if isinstance(v, list):
        return b"[" + b"".join(_w(x) for x in v) + b"]"
    raise TypeError(type(v))


def dumps(v) -> bytes:
    return _w(v)
