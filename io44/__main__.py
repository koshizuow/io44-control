"""io44: control a PreSonus Revelator io44 from Linux or Windows, over its USB control interface (no Universal
Control needed).

  python3 -m io44 ui [--port 8794] [--no-browser]
                                              the control page in the browser
  python3 -m io44 meters [SECONDS]            the device's meters by name (read only)
  python3 -m io44 mix                         the mixes as this computer keeps them
  python3 -m io44 mix BUS SOURCE DB           one source in one bus: BUS main | stream-a | stream-b,
                                              SOURCE playback | virtual-a | virtual-b | mic1 | headset | fx | line,
                                              DB -145 (off) .. +10
  python3 -m io44 apply                       write all the settings to the io44 (done by the page whenever the io44
                                              is there)
  python3 -m io44 fat mic1|headset PART KEY VALUE
                                              the mic's processing: PART lowcut (on, freq) | eq (on, low, pres, air) |
                                              gate (on, expander, threshold, range, attack, hold, release) | comp (on,
                                              threshold, ratio, knee, attack, release, makeup) | limit (on, ceiling,
                                              release) | voicefx (Mic 1: model 0-5, on, the effect's knobs); times ms
  pythonw -m io44 tray                        Windows: the server in the notification area, with a menu (open
                                              the page, write the settings, start with Windows, Universal
                                              Control's service off/on)
  python3 -m io44 service install|uninstall   run the page's server from login: the io44 gets its settings
                                              whenever it is plugged in (while it runs, the command line cannot
                                              open the io44: use the page)
  python3 -m io44 status                      what the io44 reports (gains, Main volume, the blend)
  python3 -m io44 gain mic1|headset|line DB   input gain (Mic 1 0..60, Headset 0..30, Line In -12..+12)
  python3 -m io44 dsp mic1|headset on|off     the mic's processing on, or bypassed
  python3 -m io44 record mic1|headset processed|dry
                                              what the computer records from the mic and the stream mixes get:
                                              after its processing or before it
  python3 -m io44 pan mic1|headset|line -1..1    left .. right
  python3 -m io44 main-volume 0..100          Main's volume in % (the front knob)
  python3 -m io44 phones-volume 0..100        headphone volume in %
  python3 -m io44 phones mute|unmute
  python3 -m io44 mono main|stream-a|stream-b on|off
  python3 -m io44 reverb style ambience|room|studio|club|plate|hall|theatre|arena
  python3 -m io44 reverb amount 0..1          how much of the mics goes to the reverb (0 off, 0.5 the style's own)
  python3 -m io44 reverb [mix=0..1] [predelay=MS] [size=0..1] [hp=HZ]
                                              the reverb's own settings (a style no more: "custom")
  python3 -m io44 rate [44100|48000|88200|96000|auto]
                                              the io44's sample rate (a WirePlumber rule; auto = the system's)
  python3 -m io44 pipewire print|install|uninstall
                                              the io44's channels as named devices in PipeWire (Mic 1, Headset,
                                              Line In, Stream Mix A/B, Playback, Virtual A/B)
"""
import json
import os
import struct
import subprocess
import sys
import time

from . import device, pwconf, settings
from .device import BUSES, SOURCES, BUS_NAMES, SOURCE_NAMES, Io44

# the settings kept on this computer: ~/.config/io44-control on Linux, %APPDATA%\io44-control on Windows
STATE = os.path.join((os.environ.get("APPDATA") if sys.platform == "win32" else None) or os.environ.get("XDG_CONFIG_HOME")
                     or os.path.expanduser("~/.config"), "io44-control", "state.json")
# which plugging-in of the io44 last got the settings (its USB bus and address): the io44 starts on its own defaults
# each time it is plugged in, and only a running page server writes them then by itself
APPLIED = os.path.join(os.path.dirname(STATE), "applied.json")
PW_CONF = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
                       "pipewire", "pipewire.conf.d", "io44-control.conf")
WP_RATE = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
                       "wireplumber", "wireplumber.conf.d", "io44-control-rate.conf")
DEFAULT_PROFILE = "output:analog-surround-21+input:analog-surround-71"
KEY = {"mic1": "mic1", "mic2": "headset", "headset": "headset", "line": "line"}


def load() -> dict:
    """the settings; none yet, or an older file (which held Universal Control's): a neutral start, marked "fresh" so
    the gains and the blend are read from the io44 when it is next there (the older file kept beside it)"""
    try:
        s = json.load(open(STATE))
    except (OSError, ValueError):
        s = None
    if s and s.get("v") == settings.VERSION:
        return settings.fill_defaults(s)
    new = settings.default_state()
    new["fresh"] = True
    if s:
        old = STATE.replace(".json", ".v1.json")
        if not os.path.exists(old):
            os.replace(STATE, old)
        # kept: what was io44-control's own (the bypass, the headphones), not Universal Control's
        for k, v in (s.get("bypass") or {}).items():
            name = settings.INPUTS[int(k)]
            if name in settings.MICS:
                new["inputs"][name]["dsp"] = not v
        for k in ("phones-volume", "phones-mute"):
            if k in (s.get("set") or {}):
                new[k] = s["set"][k]
    save(new)
    return new


def save(s: dict):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    json.dump(s, open(tmp, "w"), indent=1)
    os.replace(tmp, STATE)


def view(s: dict) -> dict:
    return settings.view(s)


def note_mix(s: dict, bus: int, src: int, g: float):
    settings.set_mix(s, bus, src, g)


def read_device(d: Io44, s: dict):
    """a fresh start takes the gains and the blend as the io44 has them"""
    st = d.state()
    for ch, g in st["gain"].items():
        s["inputs"][settings.INPUTS[ch]]["gain"] = float(g)
    b = d.blend()
    if b is not None:
        s["blend"] = b
    s.pop("fresh", None)


def apply_all(d: Io44, s: dict) -> int:
    if s.get("fresh"):
        read_device(d, s)
    else:
        b = d.blend()
        if b is not None:
            s["blend"] = b
    n = d.write_all(settings.writes(s))
    if "phones-volume" in s:
        d.set_phones_volume(float(s["phones-volume"]) / 100)
        n += 1
    if "phones-mute" in s:
        d.set_phones_mute(bool(s["phones-mute"]))
        n += 1
    save(s)
    return n


def apply_fat(d: Io44, inp: str, section: str, key: str, value):
    """one processing setting of Mic 1 or the headset, kept and sent (that part only)"""
    s = load()
    k = KEY.get(inp)
    if k not in settings.MICS:
        raise ValueError("the processing is on Mic 1 and the headset (Line In has none)")
    if section == "voicefx":
        if k != "mic1":
            raise ValueError("the voice effects are on Mic 1 only")
        v = settings.voice_set(s, key, value)
        w = settings.voice_writes(s)
        # a knob of the same effect: its messages only (VoFx would set the effect up again: a gap and a second's wait)
        d.write_all(w if key == "model" else [x for x in w if x[2] != "VoFx"])
        save(s)
        return v
    if section == "eq" and key == "style":
        settings.eq_style(s["inputs"][k], str(value))
        d.write_all(settings.fat_writes(s, settings.INPUTS.index(k), "lowcut") + settings.fat_writes(s, settings.INPUTS.index(k), "eq"))
        save(s)
        return str(value)
    v = settings.fat_value(section, key, value)
    s["inputs"][k][section][key] = v
    # a value changed by hand: the EQ is no style's any more
    if (section == "eq" and key != "on") or (section == "lowcut" and key == "freq"):
        s["inputs"][k]["eq"]["style"] = ""
    d.write_all(settings.fat_writes(s, settings.INPUTS.index(k), section))
    save(s)
    return v


def follow_blend(d: Io44, raw: tuple):
    """the front panel's blend turned (meter slot 47 moved): Main written again (the io44 keeps the value but does not
    apply it)"""
    b = raw[47]
    if not -1.0 <= b <= 1.0:
        return
    s = load()
    if s.get("fresh") or abs(b - s["blend"]) < 0.005:
        return
    s["blend"] = b
    d.write_all(settings.blend_writes(s))
    save(s)


def mark_applied(d: Io44):
    try:
        os.makedirs(os.path.dirname(APPLIED), exist_ok=True)
        with open(APPLIED, "w") as f:
            json.dump({"where": list(d.d.where())}, f)
    except OSError:
        pass


def cli_open() -> Io44:
    """the io44 for one command. Plugged in since the settings were last written (and no page server was running to
    write them), it is still on its own defaults (2026-11-10: its gate shut Mic 1): the settings go first, 48V never."""
    d = Io44()
    try:
        prev = json.load(open(APPLIED)).get("where")
    except (OSError, ValueError):
        prev = None
    if prev != list(d.d.where()):
        print(f"io44-control: the io44 was plugged in since the settings were last written: wrote {apply_all(d, load())} "
              "settings first", file=sys.stderr, flush=True)
        mark_applied(d)
    return d


def cmd_apply():
    s = load()
    with Io44() as d:
        print(f"wrote {apply_all(d, s)} settings (Main's monitor blend {s['blend']:g})")
        mark_applied(d)


def meter_line(m: dict) -> str:
    """one line of meters: levels in dB (a list per meter), the gain reductions (gr-mic1: a dict of the parts), the
    front knob (a number). A value of another shape is shown as it is, so a new meter never stops the command."""
    out = []
    for k, v in m.items():
        if isinstance(v, (list, tuple)):
            out.append(f"{k} " + "/".join(f"{x:.0f}" if isinstance(x, (int, float)) else str(x) for x in v))
        elif isinstance(v, dict):
            out.append(f"{k} " + " ".join(f"{p} {x:.1f}" if isinstance(x, (int, float)) else f"{p} {x}" for p, x in v.items()))
        elif isinstance(v, float):
            out.append(f"{k} {v:.2f}")
        else:
            out.append(f"{k} {v}")
    return "  ".join(out)


def cmd_meters(secs: float):
    with cli_open() as d:
        end = time.time() + secs
        while time.time() < end:
            m = d.meters()
            print(meter_line(m), flush=True)
            time.sleep(0.2)


def cmd_mix(args):
    s = load()
    if not args:
        for b, srcs in sorted(settings.mixes(s).items()):
            print(BUS_NAMES[b] + ": " + ", ".join(f"{SOURCE_NAMES[k]} {v:g} dB" for k, v in srcs))
        return
    if len(args) != 3 or args[0] not in BUSES or args[1] not in SOURCES:
        sys.exit(__doc__)
    bus, src, g = BUSES[args[0]], SOURCES[args[1]], float(args[2])
    with cli_open() as d:
        d.set_mix(bus, [(src, g)])
    note_mix(s, bus, src, g)
    save(s)
    print(f"{BUS_NAMES[bus]}: {SOURCE_NAMES[src]} {g:g} dB")


def apply_setting(d: Io44, what: str, key: str, value):
    """one setting by name, sent and kept (the io44 does not report these, except gain and Main's volume)"""
    s = load()
    k = KEY.get(key, key)
    if what == "gain":
        d.set_gain(device.INPUTS[key], float(value))
        s["inputs"][k]["gain"] = float(value)
    elif what == "dsp":
        if k not in settings.MICS:
            raise ValueError("Line In has no processing")
        d.set_dsp(device.INPUTS[key], 1.0 if value else 0.0)
        s["inputs"][k]["dsp"] = bool(value)
    elif what in ("record_processed", "dawpost"):
        if k not in settings.MICS:
            raise ValueError("Line In has no processing")
        d.set_dawpost(device.INPUTS[key], bool(value))
        s["inputs"][k]["record_processed"] = bool(value)
    elif what == "pan":
        v = max(-1.0, min(1.0, float(value)))
        d.set_pan(device.INPUTS[key], (v + 1) / 2)
        s["inputs"][k]["pan"] = v
    elif what == "main-volume":
        d.set_main_volume(float(value) / 100)
        return value  # the front knob: the io44 reports it
    elif what == "phones-volume":
        d.set_phones_volume(float(value) / 100)
        s["phones-volume"] = float(value)
    elif what == "phones-mute":
        d.set_phones_mute(bool(value))
        s["phones-mute"] = bool(value)
    elif what == "mono":
        d.set_mono(BUSES[key], bool(value))
        s["mono"][key] = bool(value)
    elif what == "phantom":
        # 48V on Mic 1: sent only when asked (ribbon and tube mics can be damaged), never written by apply; the page
        # asks first. Kept only to show what was last sent (the io44 does not report it)
        d.set_phantom(0, bool(value))
        s["phantom"] = bool(value)
    elif what == "blend":
        # Main's monitor blend (-1 inputs only .. +1 playback only): the device keeps it (the front panel shows it from
        # here on), Main follows
        b = max(-1.0, min(1.0, float(value)))
        device.finite(b)
        d._set(device.APPL, 0, "Para", struct.pack("<If", 10, b))
        s["blend"] = b
        d.write_all(settings.blend_writes(s))
        value = b
    elif what == "reverb":
        # {"style": "hall"}, {"amount": 0.5} or the reverb's own settings (mix, predelay, size, hp)
        for kk, v in value.items():
            settings.reverb_set(s, kk, v)
        send = settings.reverb_send(s)
        d.write_all([settings.reverb_write(s)] + [(0, 0, "Para", struct.pack("<If", 1, max(settings.OFF_DB, send)), ci)
                                                  for ci in (0, 1)] + [("mprm", b, g) for b, g in settings.mixes(s).items()])
        value = s["reverb"]
    else:
        raise ValueError(what)
    save(s)
    return value


def cmd_set(a):
    try:
        _cmd_set(a)
    except ValueError as e:
        sys.exit(str(e))


def _cmd_set(a):
    what = a[0]
    on = {"on": True, "off": False, "mute": True, "unmute": False, "processed": True, "dry": False}
    with cli_open() as d:
        if what == "record" and len(a) == 3 and a[1] in device.INPUTS and a[2] in on:
            print("record", a[1], "processed" if apply_setting(d, "record_processed", a[1], on[a[2]]) else "dry")
        elif what in ("gain", "pan") and len(a) == 3 and a[1] in device.INPUTS:
            print(what, a[1], apply_setting(d, what, a[1], float(a[2])))
        elif what == "dsp" and len(a) == 3 and a[1] in device.INPUTS and a[2] in on:
            print(what, a[1], apply_setting(d, what, a[1], on[a[2]]))
        elif what in ("main-volume", "phones-volume") and len(a) == 2:
            print(what, apply_setting(d, what, "", float(a[1])))
        elif what == "phones" and len(a) == 2 and a[1] in on:
            print("phones mute", apply_setting(d, "phones-mute", "", on[a[1]]))
        elif what == "mono" and len(a) == 3 and a[1] in BUSES and a[2] in on:
            print("mono", a[1], apply_setting(d, "mono", a[1], on[a[2]]))
        elif what == "reverb":
            ch = {}
            if len(a) == 3 and a[1] in ("style", "amount"):
                ch[a[1]] = a[2] if a[1] == "style" else float(a[2])
            else:
                for x in a[1:]:
                    kk, v = x.split("=")
                    ch[kk] = float(v) / 1000 if kk == "predelay" else float(v)
            print("reverb", apply_setting(d, "reverb", "", ch))
        else:
            sys.exit(__doc__)


def cmd_status():
    with cli_open() as d:
        st = d.state()
        b = d.blend()
    print("from the io44: " + ", ".join(f"{device.INPUT_NAMES[c]} gain {g:g} dB" for c, g in st["gain"].items())
          + f", Main volume {st['main'] * 100:.0f}%" + (f", monitor blend {b:+.2f}" if b is not None else ""))


def pactl(*a):
    return subprocess.run(["pactl", *a], capture_output=True, text=True)


def pw_set(install: bool) -> str:
    card = pwconf.find_card()
    if install:
        os.makedirs(os.path.dirname(PW_CONF), exist_ok=True)
        open(PW_CONF, "w").write(pwconf.config(card))
        subprocess.run(["systemctl", "--user", "restart", "pipewire", "pipewire-pulse", "wireplumber"])
        # the profile after the restart: WirePlumber puts back the one it remembers when it starts (2026-11-10: set
        # before the restart, the card came back on its surround profile and the named devices read nothing)
        out = pwconf.node_names(card)[0]
        for _ in range(100):  # PipeWire coming back
            pactl("set-card-profile", card, "pro-audio")
            if pactl("set-sink-volume", out, *["100%"] * 6).returncode == 0 and "io44.playback" in pactl("list", "sinks", "short").stdout:
                break
            time.sleep(0.2)
        else:
            raise SystemExit("the io44 did not come back on its Pro Audio profile")
        pactl("set-default-sink", "io44.playback")
        return f"wrote {PW_CONF}; the io44 is on its Pro Audio profile, the default output is io44 Playback"
    if os.path.exists(PW_CONF):
        os.remove(PW_CONF)
    subprocess.run(["systemctl", "--user", "restart", "pipewire", "pipewire-pulse", "wireplumber"])
    for _ in range(50):
        if pactl("set-card-profile", card, DEFAULT_PROFILE).returncode == 0:
            break
        time.sleep(0.2)
    return f"removed {PW_CONF}; the io44 is back on {DEFAULT_PROFILE}"


def cmd_pipewire(what: str):
    if what == "print":
        print(pwconf.config(pwconf.find_card()), end="")
    elif what in ("install", "uninstall"):
        print(pw_set(what == "install"))
    else:
        sys.exit(__doc__)


def current_rate() -> int | None:
    """the rate set from here (None: the system's)"""
    try:
        import re
        return int(re.search(r"audio.rate = (\d+)", open(WP_RATE).read()).group(1))
    except (OSError, AttributeError):
        return None


def rate_set(rate: int | None) -> str:
    if rate is None:
        if os.path.exists(WP_RATE):
            os.remove(WP_RATE)
    else:
        if rate not in pwconf.RATES:
            raise SystemExit(f"rate: one of {', '.join(map(str, pwconf.RATES))} or auto")
        os.makedirs(os.path.dirname(WP_RATE), exist_ok=True)
        open(WP_RATE, "w").write(pwconf.rate_rule(rate))
    subprocess.run(["systemctl", "--user", "restart", "pipewire", "pipewire-pulse", "wireplumber"])
    return f"the io44 runs at {rate} Hz" if rate else "the io44 follows the system's rate"


def run_briefly():
    """the io44 opened for half a second (silence to io44 Playback, or its raw output): PipeWire opens a device only
    while something uses it, so a new rate takes effect on the device only then (2026-11-10: the repair changed the rule
    and back with the io44 idle, and it never ran at the other rate)"""
    import tempfile
    import wave
    names = pactl("list", "sinks", "short").stdout
    target = "io44.playback" if "io44.playback" in names else next(
        (l.split()[1] for l in names.splitlines() if "Revelator" in l), None)
    if not target:
        return
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(b"\0" * 48000 * 2)
    try:
        subprocess.run(["pw-play", "--target", target, path], timeout=10, capture_output=True)
    finally:
        os.remove(path)


def wait_for_io44(secs: float = 15.0):
    """after a PipeWire restart: until the io44's output is back"""
    end = time.time() + secs
    while time.time() < end:
        if "io44.playback" in pactl("list", "sinks", "short").stdout or "Revelator" in pactl("list", "sinks", "short").stdout:
            return
        time.sleep(0.3)


def repair_rate():
    """every mix silent: the io44 run at another rate and back, which starts its DSP over (the rule as it was after,
    "the system's rate" included)"""
    cur = current_rate()
    for r in (44100 if cur != 44100 else 48000, cur):
        rate_set(r)
        wait_for_io44()
        time.sleep(1.0)
        run_briefly()


def device_rate() -> str:
    """what the io44 runs at now (the kernel's view; nothing while no program uses it)"""
    try:
        import glob
        for f in glob.glob("/proc/asound/card*/stream0"):
            t = open(f).read()
            if "Revelator IO 44" in t:
                import re
                m = re.findall(r"Momentary freq = (\d+) Hz", t)
                return ", ".join(sorted(set(m))) + " Hz" if m else "idle"
    except OSError:
        pass
    return "unknown"


def cmd_ui(port: int, open_browser: bool):
    from . import web
    if open_browser:
        if sys.platform == "win32":
            os.startfile(f"http://127.0.0.1:{port}/")
        else:
            subprocess.Popen(["xdg-open", f"http://127.0.0.1:{port}/"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    def on_open(d: Io44):
        # as Universal Control does: the whole state to the io44 when it is (again) there: started, plugged in, or
        # back after it was unplugged or powered off (it starts on its own defaults then)
        print(f"io44-control: the io44 is here: wrote {apply_all(d, load())} settings", flush=True)
        mark_applied(d)
    if sys.platform == "win32":  # the sample rate through the USB audio driver (rate_win), no PipeWire
        from . import rate_win

        def rget():
            try:
                r = rate_win.current()
                return {"set": r, "now": f"{r} Hz", "rates": rate_win.rates()}
            except OSError as e:
                return {"set": None, "now": str(e)}
        rate_get, rset = rget, (lambda r: rate_win.set_rate(int(r)) if r else "")
    else:
        rate_get, rset = (lambda: {"set": current_rate(), "now": device_rate()}), rate_set
    web.serve(port, load, save, apply_setting, lambda: os.path.exists(PW_CONF), pw_set,
              rate_get, rset, view, note_mix, on_open, apply_fat,
              follow_blend, lambda d: apply_all(d, load()), repair=None if sys.platform == "win32" else repair_rate)


UNIT = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "systemd", "user", "io44-control.service")


def cmd_service(what: str):
    """the page's server as a user service: running from login, so the io44 gets its settings whenever it is plugged in"""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if what == "install":
        os.makedirs(os.path.dirname(UNIT), exist_ok=True)
        open(UNIT, "w").write(f"""[Unit]
Description=io44-control: the Revelator io44's settings written when it is plugged in; its page at http://127.0.0.1:8794/

[Service]
WorkingDirectory={here}
ExecStart={sys.executable} -m io44 ui --no-browser
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
""")
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", "--now", "io44-control.service"], check=True)
        print(f"installed {UNIT}: running now and from every login (the page: http://127.0.0.1:8794/)")
    elif what == "uninstall":
        subprocess.run(["systemctl", "--user", "disable", "--now", "io44-control.service"])
        if os.path.exists(UNIT):
            os.remove(UNIT)
        subprocess.run(["systemctl", "--user", "daemon-reload"])
        print("removed the service")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["meters"]:
        cmd_meters(float(a[1]) if len(a) > 1 else 3)
    elif a[:1] == ["mix"]:
        cmd_mix(a[1:])
    elif a[:1] == ["ui"]:
        cmd_ui(int(a[a.index("--port") + 1]) if "--port" in a else 8794, "--no-browser" not in a)
    elif a[:1] == ["fat"] and len(a) == 5:
        try:
            with cli_open() as d:
                print(a[1], a[2], a[3], apply_fat(d, a[1], a[2], a[3], a[4]))
        except ValueError as e:
            sys.exit(str(e))
    elif a[:1] == ["tray"]:
        from . import tray_win
        if sys.platform == "win32":  # pythonw has no console: the server's messages go to a log beside the settings
            os.makedirs(os.path.dirname(STATE), exist_ok=True)
            sys.stdout = sys.stderr = open(os.path.join(os.path.dirname(STATE), "io44-control.log"), "a", buffering=1)
        tray_win.run(lambda: cmd_ui(8794, False))
    elif a[:1] == ["service"] and len(a) == 2:
        cmd_service(a[1])
    elif a[:1] == ["apply"]:
        cmd_apply()
    elif a[:1] == ["status"]:
        cmd_status()
    elif a[:1] and a[0] in ("gain", "dsp", "record", "pan", "main-volume", "phones-volume", "phones", "mono", "reverb"):
        cmd_set(a)
    elif a[:1] == ["rate"]:
        if len(a) == 1:
            print(f"set: {current_rate() or 'the system rate'}; running: {device_rate()}")
        else:
            if a[1] != "auto" and a[1] not in ("44100", "48000", "88200", "96000"):
                sys.exit("rate: 44100, 48000, 88200, 96000 or auto")
            print(rate_set(None if a[1] == "auto" else int(a[1])))
    elif a[:1] == ["pipewire"] and len(a) == 2:
        cmd_pipewire(a[1])
    else:
        print(__doc__)
