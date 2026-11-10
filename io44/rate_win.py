"""Windows: the io44's sample rate through its USB audio driver's API (PreSonus' build of the Thesycon driver, the
library installed with Universal Control: Drivers\\DSPUSBSeries\\x64\\PaeDSPUSBapi_x64.dll), as Universal Control
sets it. Checked on the Windows test PC (2026-11-09): one device, rates 44100, 48000, 88200, 96000."""
import ctypes as C
import glob
import os

PATTERNS = [os.path.join(os.environ.get(v, ""), *p) for v in ("ProgramFiles", "ProgramW6432")
            for p in (("Fender", "Universal Control", "Drivers", "DSPUSBSeries", "x64", "PaeDSPUSBapi_x64.dll"),
                      ("PreSonus", "Universal Control", "Drivers", "DSPUSBSeries", "x64", "PaeDSPUSBapi_x64.dll"))]


def _dll():
    for p in PATTERNS:
        for f in glob.glob(p):
            return C.WinDLL(f)
    raise OSError("the io44's driver library (PaeDSPUSBapi_x64.dll, installed with Universal Control) was not found")


def _open():
    d = _dll()
    d.TUSBAUDIO_EnumerateDevices()
    if d.TUSBAUDIO_GetDeviceCount() < 1:
        raise OSError("the driver sees no io44")
    h = C.c_void_p()
    st = d.TUSBAUDIO_OpenDeviceByIndex(C.c_uint(0), C.byref(h))
    if st != 0:
        raise OSError(f"the driver did not open the io44 (status {st & 0xffffffff:#x})")
    return d, h


def rates() -> list:
    d, h = _open()
    try:
        arr, n = (C.c_uint * 32)(), C.c_uint()
        d.TUSBAUDIO_GetSupportedSampleRates(h, C.c_uint(32), arr, C.byref(n))
        return list(arr[:n.value])
    finally:
        d.TUSBAUDIO_CloseDevice(h)


def current() -> int:
    d, h = _open()
    try:
        r = C.c_uint()
        st = d.TUSBAUDIO_GetCurrentSampleRate(h, C.byref(r))
        if st != 0:
            raise OSError(f"sample rate not read (status {st & 0xffffffff:#x})")
        return r.value
    finally:
        d.TUSBAUDIO_CloseDevice(h)


def set_rate(rate: int) -> str:
    d, h = _open()
    try:
        ok = []
        arr, n = (C.c_uint * 32)(), C.c_uint()
        d.TUSBAUDIO_GetSupportedSampleRates(h, C.c_uint(32), arr, C.byref(n))
        ok = list(arr[:n.value])
        if rate not in ok:
            raise ValueError(f"rate: one of {', '.join(map(str, ok))}")
        st = d.TUSBAUDIO_SetSampleRate(h, C.c_uint(rate))
        if st != 0:
            raise OSError(f"sample rate not set (status {st & 0xffffffff:#x})")
        return f"the io44 runs at {rate} Hz"
    finally:
        d.TUSBAUDIO_CloseDevice(h)
