#!/usr/bin/env python3
"""ucctl.py : read and set a PreSonus interface's parameters through Universal Control's service (UCNet over TCP,
the service PreSonusHardwareAccessService on port 49670; found on the Windows test PC's Revelator IO 44 with UC 5.1.1).

  ucctl.py HOST dump OUT.json            the whole state (the device's "Synchronize" tree) to a file
  ucctl.py HOST get NAME [NAME ...]      values, e.g. main/ch1/mute global/mainOutVolume
  ucctl.py HOST set NAME=VALUE [...]     set floats (0..1, as the interface keeps them), prints before and after
  ucctl.py HOST setup [RATE] [BLOCK]     the audio setup (sample rate, buffer size): prints it, or sets it

The handshake is the one Universal Control's window uses (recorded with loopcap.ps1): per channel a UM (two bytes:
a UDP port) and a JM Subscribe with clientEncoding 23117. Channel 6b/67 is the device: its first ZM is the whole
state, then PV messages carry changes both ways: name, three zero bytes, float32 LE. Values are what the device
keeps (normalised 0..1, not dB): read them first, set what was read to put anything back. Channel 64/68 is the
device list: its UpdateDevices carries the audio setup (AudioDeviceSetup), changed by JM InvokeMethod
"setupAudioDevice" with arg0 the device index and arg1 the whole setup (recorded from the window's sample-rate
menu). Pressing the active Fat Channel preset in the window is only PV line/ch1/bypassDSP.
"""
import json
import socket
import struct
import sys
import time
import zlib

PORT = 49670
CHANNELS = (("00006600", "6a006600"), ("00006800", "64006800"), ("00006700", "6b006700"))
DEVICE = bytes.fromhex("6b006700")


def pkt(code, cb, payload):
    body = code + cb + payload
    return b"UC\x00\x01" + struct.pack("<H", len(body)) + body


def jm(cb, obj):
    j = json.dumps(obj).encode()
    return pkt(b"JM", cb, struct.pack("<I", len(j)) + j)


def messages(buf):
    """complete UC messages in buf: [(code, channel bytes, payload)], the rest"""
    out, j = [], 0
    while j + 6 <= len(buf):
        if buf[j:j + 4] != b"UC\x00\x01":
            k = buf.find(b"UC\x00\x01", j + 1)
            if k < 0:
                return out, b""
            j = k
            continue
        n = struct.unpack("<H", buf[j + 4:j + 6])[0]
        if j + 6 + n > len(buf):
            break
        body = buf[j + 6:j + 6 + n]
        out.append((body[:2], body[2:6], body[6:]))
        j += 6 + n
    return out, buf[j:]


class UC:
    def __init__(self, host):
        self.s = socket.create_connection((host, PORT), timeout=5)
        for um, cb in CHANNELS:
            self.s.sendall(pkt(b"UM", bytes.fromhex(um), bytes.fromhex("b6c5")))
            self.s.sendall(jm(bytes.fromhex(cb), {"id": "Subscribe", "clientName": "", "clientInternalName": "",
                                                  "clientType": "PC", "clientDescription": "stream-mic",
                                                  "clientIdentifier": "stream-mic", "clientOptions": "",
                                                  "clientEncoding": 23117}))
        self.buf, self.state, self.pv, self.devices = b"", None, {}, None

    def pump(self, secs):
        end = time.time() + secs
        self.s.settimeout(0.3)
        while time.time() < end:
            try:
                d = self.s.recv(1 << 20)
                if not d:
                    break
                self.buf += d
            except socket.timeout:
                for _, cb in CHANNELS:
                    self.s.sendall(pkt(b"KA", bytes.fromhex(cb), b""))
            msgs, self.buf = messages(self.buf)
            for code, cb, pl in msgs:
                if code == b"ZM":
                    t = json.loads(zlib.decompress(pl[4:]))
                    if t.get("id") == "Synchronize":
                        self.state = t
                    elif t.get("id") == "UpdateDevices":
                        self.devices = t["deviceList"]
                elif code == b"JM":
                    t = json.loads(pl[4:])
                    if t.get("id") == "DevicePropertyChanged" and self.devices:
                        props = self.devices[t["deviceIndex"]]["properties"]
                        for i, p in enumerate(props):
                            if p.get("__typeid") == t["deviceProperty"].get("__typeid"):
                                props[i] = t["deviceProperty"]
                elif code == b"PV":
                    name, _, rest = pl.partition(b"\x00")
                    self.pv[name.decode()] = struct.unpack("<f", rest[2:6])[0]
            if self.state is not None and secs < 0:
                return

    def wait_state(self, secs=6):
        end = time.time() + secs
        while self.state is None and time.time() < end:
            self.pump(0.5)
        if self.state is None:
            raise SystemExit("no state from the service")
        return self.state

    def set(self, name, value):
        self.s.sendall(pkt(b"PV", DEVICE, name.encode() + b"\x00\x00\x00" + struct.pack("<f", value)))

    def setup(self):
        """the first device's AudioDeviceSetup"""
        return next(p for p in self.devices[0]["properties"] if p.get("__typeid") == "AudioDeviceSetup")

    def set_setup(self, **kw):
        s = dict(self.setup(), **kw)
        s["flags"] = 0  # as the window sends it
        self.s.sendall(jm(bytes.fromhex("64006800"), {"id": "InvokeMethod", "url": "", "method": "setupAudioDevice",
                                                      "argc": 2, "arg0": 0, "arg1": s}))

    def close(self):
        self.s.close()


def flat(node, path=""):
    for k, v in (node.get("values") or {}).items():
        yield path + k, v
    for k, c in (node.get("children") or {}).items():
        yield from flat(c, path + k + "/")


def main():
    host, cmd, args = sys.argv[1], sys.argv[2], sys.argv[3:]
    uc = UC(host)
    vals = dict(flat(uc.wait_state()))
    if cmd == "dump":
        json.dump(uc.state, open(args[0], "w"), ensure_ascii=False, indent=1)
        print(len(vals), "values ->", args[0])
    elif cmd == "get":
        for n in args:
            print(n, vals.get(n, "(none)"))
    elif cmd == "set":
        for a in args:
            n, v = a.split("=", 1)
            if n not in vals:
                raise SystemExit(f"{n}: no such value")
            print(f"{n}: {vals[n]} -> {float(v)}")
            uc.set(n, float(v))
        uc.pump(1.5)
        for a in args:
            n = a.split("=", 1)[0]
            print(f"{n}: now {uc.pv.get(n, '(no echo)')}")
    elif cmd == "setup":
        while uc.devices is None:
            uc.pump(0.5)
        if args:
            kw = {"sampleRate": int(args[0])}
            if len(args) > 1:
                kw["blockSize"] = int(args[1])
            uc.set_setup(**kw)
            uc.pump(3)
        s = uc.setup()
        print("sampleRate", s["sampleRate"], "blockSize", s["blockSize"])
    uc.close()


if __name__ == "__main__":
    main()
