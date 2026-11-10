"""The control page: a small local web server (standard library only) that owns the io44's control interface and
serves ui/. Started by `python3 -m io44 ui`; the page is at http://127.0.0.1:8794/.

  GET  /api/state   the settings kept here (mixes, settings, the mics' processing), the names, the rate, PipeWire
  GET  /api/meters  the meters by name (dB), the Main knob
  POST /api/mix     {"bus": 1, "source": 3, "db": -6.0}: one source in one bus
  POST /api/set     {"what": "gain", "key": "mic1", "value": 30}: one setting (see __main__.apply_setting)
  POST /api/pipewire {"install": true|false}
  POST /api/rate    {"rate": 48000} or {"rate": "auto"}: the io44's sample rate (Linux: a PipeWire rule, restarts
                    PipeWire; Windows: through the USB audio driver); the whole state written again after
  POST /api/fat     {"input": "mic1", "section": "eq", "key": "pres", "value": 2}: one processing setting
  POST /api/apply   the whole state to the io44 now
  POST /api/repair  every mix silent: the sample rate away and back (the DSP starts over), then the whole state

The io44 is looked for every 2 s; each time it is opened (started, plugged in, back after being unplugged) it gets
the whole state, as Universal Control's service does.

Only one program may hold the control interface: the command line's `mix` and `meters` wait until this is closed.
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import device
from .device import BUS_NAMES, SOURCE_NAMES, Io44
from .usb import UsbError

UI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".woff2": "font/woff2", ".svg": "image/svg+xml"}


class Link:
    """the device, opened when needed and again after it was unplugged; one request at a time. on_open(dev) runs each
    time it is opened (the whole state written: it starts on its own defaults after being unplugged)"""
    def __init__(self, on_open=None):
        self.lock = threading.Lock()
        self.dev = None
        self.error = ""
        self.on_open = on_open

    def run(self, f):
        with self.lock:
            for attempt in (0, 1):
                try:
                    if self.dev is None:
                        self.dev = Io44()
                        if self.on_open:
                            self.on_open(self.dev)
                    r = f(self.dev)
                    self.error = ""
                    return r
                except (UsbError, OSError) as e:
                    self.error = str(e)
                    if self.dev:
                        try:
                            self.dev.close()
                        except Exception:
                            pass
                    self.dev = None
            return None


def serve(port: int, state_load, state_save, apply_setting, pipewire_installed, pipewire_set, rate_get, rate_set,
          view, note_mix, on_open=None, apply_fat=None, follow_blend=None, apply_now=None, repair=None):
    link = Link(on_open)

    # the io44 looked at 4 times a second, page open or not: plugged in (or back after being unplugged) it gets the
    # whole state at once, not only when a page asks; the front panel's blend turned, Main is written again
    def watch():
        import time

        def look(d):
            v = d.raw_meters()
            if follow_blend:
                follow_blend(d, v)
        while True:
            link.run(look)
            time.sleep(0.25)
    threading.Thread(target=watch, name="io44-watch", daemon=True).start()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body, ctype="application/json"):
            b = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            p = self.path.split("?")[0]
            if p == "/api/state":
                s = state_load()
                v = view(s)
                return self.send(200, dict(v, buses=BUS_NAMES, sources=SOURCE_NAMES, platform=__import__("sys").platform,
                                           fresh=bool(s.get("fresh")), pipewire=pipewire_installed(), rate=rate_get(),
                                           connected=link.dev is not None, error=link.error))
            if p == "/api/meters":
                m = link.run(lambda d: dict(d.meters(), device=d.state()))
                return self.send(200, {"ok": m is not None, "meters": m, "error": link.error})
            f = os.path.normpath(os.path.join(UI, (p.lstrip("/") or "index.html")))
            if not f.startswith(UI + os.sep) or not os.path.isfile(f):
                return self.send(404, {"error": "not found"})
            self.send(200, open(f, "rb").read(), TYPES.get(os.path.splitext(f)[1], "application/octet-stream"))

        def do_POST(self):
            # the page only: a request from another site carries its Origin
            origin = self.headers.get("Origin")
            if origin and origin not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}"):
                return self.send(403, {"error": "origin"})
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            except ValueError:
                return self.send(400, {"error": "json"})
            if self.path == "/api/mix":
                try:
                    bus, src, g = int(body["bus"]), int(body["source"]), float(body["db"])
                except (KeyError, TypeError, ValueError):
                    return self.send(400, {"error": "bus, source, db"})
                if bus not in BUS_NAMES or src not in SOURCE_NAMES or not -145.0 <= g <= 10.0:
                    return self.send(400, {"error": "out of range"})
                ok = link.run(lambda d: d.set_mix(bus, [(src, g)]) or True)
                if not ok:
                    return self.send(503, {"error": link.error})
                s = state_load()
                note_mix(s, bus, src, g)
                state_save(s)
                return self.send(200, {"ok": True})
            if self.path == "/api/set":
                what, key, value = body.get("what"), body.get("key") or "", body.get("value")
                err = []

                def go(d):
                    try:
                        return apply_setting(d, what, key, value)
                    except (ValueError, KeyError, TypeError) as e:
                        err.append(str(e))
                        return None
                r = link.run(go)
                if err:
                    return self.send(400, {"error": err[0]})
                if r is None:
                    return self.send(503, {"error": link.error})
                return self.send(200, {"ok": True, "value": r})
            if self.path == "/api/fat" and apply_fat:
                err = []

                def go(d):
                    try:
                        return {"value": apply_fat(d, body.get("input"), body.get("section"), body.get("key"), body.get("value"))}
                    except (ValueError, KeyError, TypeError) as e:
                        err.append(str(e))
                        return None
                r = link.run(go)
                if err:
                    return self.send(400, {"error": err[0]})
                if r is None:
                    return self.send(503, {"error": link.error})
                return self.send(200, dict(r, ok=True))
            if self.path == "/api/repair" and apply_now:
                # every mix silent (a NaN in the reverb, left by Universal Control): the DSP started over by a sample
                # rate change and back, then the whole state; no restart of the computer needed (2026-11-09)
                try:
                    if repair:  # Linux: the io44 has to be running for a rate to reach it (__main__.repair_rate)
                        repair()
                    else:  # Windows: the driver changes the device's rate at once
                        cur = rate_get().get("set")
                        rate_set(44100 if cur != 44100 else 48000)
                        rate_set(cur)
                except (SystemExit, ValueError, OSError) as e:
                    return self.send(400, {"error": str(e)})
                n = link.run(apply_now)
                return self.send(200, {"ok": True, "written": n})
            if self.path == "/api/apply" and apply_now:
                n = link.run(apply_now)
                if n is None:
                    return self.send(503, {"error": link.error})
                return self.send(200, {"ok": True, "written": n})
            if self.path == "/api/pipewire":
                try:
                    msg = pipewire_set(bool(body.get("install")))
                except SystemExit as e:
                    return self.send(500, {"error": str(e)})
                return self.send(200, {"ok": True, "message": msg, "pipewire": pipewire_installed()})
            if self.path == "/api/rate":
                r = body.get("rate")
                try:
                    msg = rate_set(None if r in (None, "auto") else int(r))
                except (SystemExit, ValueError, OSError) as e:
                    return self.send(400, {"error": str(e)})
                # the io44's DSP starts over at a new rate: the whole state again, whether it kept it or not
                if apply_now:
                    link.run(apply_now)
                return self.send(200, {"ok": True, "message": msg, "rate": rate_get()})
            self.send(404, {"error": "not found"})

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    print(f"io44-control: http://127.0.0.1:{port}/  (Ctrl+C to stop)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if link.dev:
            link.dev.close()
