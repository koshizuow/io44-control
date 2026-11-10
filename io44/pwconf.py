"""A PipeWire configuration that shows the io44 as Universal Control names its channels, instead of one 6-channel
output and one 8-channel input ("Analog Surround 2.1 / 7.1", which also leaves Virtual A and B unreachable).

The card is put on its Pro Audio profile (every channel as AUX0..AUX7, in the device's order), and loopbacks make
named devices on top of it:

  outputs (sinks)   io44 Playback     -> AUX0 AUX1       (the mix's "Playback")
                    io44 Virtual A    -> AUX2 AUX3
                    io44 Virtual B    -> AUX4 AUX5
  inputs (sources)  io44 Mic 1        <- AUX0 (mono)
                    io44 Headset      <- AUX1 (mono)
                    io44 Line In      <- AUX2 AUX3
                    io44 Stream Mix A <- AUX4 AUX5
                    io44 Stream Mix B <- AUX6 AUX7

Each loopback waits for its io44 node rather than moving elsewhere or going away (node.dont-fallback with
node.linger): with node.dont-reconnect, WirePlumber destroyed the loopback when the io44 was unplugged and nothing made
it again (2026-11-10).
The order was measured on the device (2026-11-09): a tone on each output channel in turn on the io44's own
playback meters, the capture channels against the mixes (turning Mic 1 off in a mix silences that mix's pair).
"""
import re
import subprocess

OUTS = [("playback", "Playback", ["AUX0", "AUX1"]), ("virtual-a", "Virtual A", ["AUX2", "AUX3"]),
        ("virtual-b", "Virtual B", ["AUX4", "AUX5"])]
INS = [("mic1", "Mic 1", ["AUX0"]), ("mic2", "Headset", ["AUX1"]), ("line-in", "Line In", ["AUX2", "AUX3"]),
       ("stream-mix-a", "Stream Mix A", ["AUX4", "AUX5"]), ("stream-mix-b", "Stream Mix B", ["AUX6", "AUX7"])]
CARD_RE = r"alsa_card\.usb-PreSonus_Revelator_IO_44_[A-Za-z0-9]+-00"


def find_card() -> str:
    out = subprocess.run(["pactl", "list", "cards", "short"], capture_output=True, text=True).stdout
    m = re.search(CARD_RE, out)
    if not m:
        raise SystemExit("no Revelator io44 found (pactl list cards short)")
    return m.group(0)


def node_names(card: str) -> tuple[str, str]:
    base = card.replace("alsa_card.", "")
    return f"alsa_output.{base}.pro-output-0", f"alsa_input.{base}.pro-input-0"


def pos(p):
    return "[ " + " ".join(p) + " ]"


def config(card: str) -> str:
    out_node, in_node = node_names(card)
    mods = []
    for key, name, ch in OUTS:
        stereo = "[ FL FR ]" if len(ch) == 2 else "[ MONO ]"
        mods.append(f"""  {{ name = libpipewire-module-loopback
    args = {{
      node.description = "io44 {name}"
      capture.props = {{
        node.name = "io44.{key}"
        media.class = Audio/Sink
        audio.position = {stereo}
      }}
      playback.props = {{
        node.name = "io44.{key}.out"
        audio.position = {pos(ch)}
        target.object = "{out_node}"
        stream.dont-remix = true
        node.passive = true
        node.dont-fallback = true
        node.linger = true
      }}
    }}
  }}""")
    for key, name, ch in INS:
        shape = "[ FL FR ]" if len(ch) == 2 else "[ MONO ]"
        mods.append(f"""  {{ name = libpipewire-module-loopback
    args = {{
      node.description = "io44 {name}"
      capture.props = {{
        node.name = "io44.{key}.in"
        audio.position = {pos(ch)}
        target.object = "{in_node}"
        stream.dont-remix = true
        node.passive = true
        node.dont-fallback = true
        node.linger = true
      }}
      playback.props = {{
        node.name = "io44.{key}"
        media.class = Audio/Source
        audio.position = {shape}
      }}
    }}
  }}""")
    return ("# io44-control: the Revelator io44's channels as named devices (python3 -m io44 pipewire)\n"
            "# The card must be on its Pro Audio profile.\n"
            "context.modules = [\n" + "\n".join(mods) + "\n]\n")


RATES = (44100, 48000, 88200, 96000)


def rate_rule(rate: int) -> str:
    """a WirePlumber rule that opens the io44's ALSA devices at RATE (PipeWire converts when the rest of the system
    runs at another rate). The io44 supports 44.1, 48, 88.2 and 96 kHz (its USB descriptors)."""
    assert rate in RATES
    return ("# io44-control: the io44's sample rate (python3 -m io44 rate)\n"
            "monitor.alsa.rules = [\n"
            "  { matches = [ { node.name = \"~alsa_(input|output)\\\\.usb-PreSonus_Revelator_IO_44_.*\" } ]\n"
            f"    actions = {{ update-props = {{ audio.rate = {rate} audio.allowed-rates = [ {rate} ] }} }}\n"
            "  }\n]\n")
