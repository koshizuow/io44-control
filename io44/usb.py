"""The io44's control interface over libusb-1.0 (ctypes, no Python packages): interface 5, bulk 0x01 out, 0x81 in.
The audio interfaces stay with the kernel's snd-usb-audio; only the vendor interface is claimed."""
import ctypes as C
import ctypes.util
import os
import sys

VID, PID = 0x194F, 0x0424
IFACE, EP_OUT, EP_IN = 5, 0x01, 0x81  # interface 5 alternate setting 1



def _load():
    if sys.platform == "win32":
        # Windows: the io44's control interface already has Microsoft's WinUSB driver, which libusb opens as it is.
        # libusb-1.0.dll beside the io44 folder, or on the PATH. Only one program may open it: stop Universal
        # Control's service (PreSonus Hardware Access Service) first.
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for f in (os.path.join(here, "libusb-1.0.dll"), "libusb-1.0.dll"):
            try:
                return C.CDLL(f)
            except OSError:
                pass
        raise OSError("libusb-1.0.dll not found (put it beside the io44 folder)")
    return C.CDLL(ctypes.util.find_library("usb-1.0") or "libusb-1.0.so.0")


_lib = _load()
_lib.libusb_open_device_with_vid_pid.restype = C.c_void_p
_lib.libusb_open_device_with_vid_pid.argtypes = [C.c_void_p, C.c_uint16, C.c_uint16]
for f in ("libusb_claim_interface", "libusb_release_interface", "libusb_kernel_driver_active"):
    getattr(_lib, f).argtypes = [C.c_void_p, C.c_int]
_lib.libusb_set_interface_alt_setting.argtypes = [C.c_void_p, C.c_int, C.c_int]
_lib.libusb_bulk_transfer.argtypes = [C.c_void_p, C.c_ubyte, C.c_void_p, C.c_int, C.POINTER(C.c_int), C.c_uint]
_lib.libusb_close.argtypes = [C.c_void_p]
_lib.libusb_error_name.restype = C.c_char_p


class UsbError(OSError):
    pass


def _check(r, what):
    if r < 0:
        raise UsbError(f"{what}: {_lib.libusb_error_name(r).decode()}")
    return r


class Device:
    def __init__(self):
        self.ctx = C.c_void_p()
        _check(_lib.libusb_init(C.byref(self.ctx)), "init")
        self.h = _lib.libusb_open_device_with_vid_pid(self.ctx, VID, PID)
        if not self.h:
            raise UsbError("Revelator io44 not found, or held by another program (Universal Control's service: stop it "
                           "from io44-control's tray menu)" if sys.platform == "win32" else
                           "Revelator io44 not found, or no permission (see udev/70-revelator-io44.rules)")
        _check(_lib.libusb_claim_interface(self.h, IFACE), "claim interface 5")
        # alternate setting 0 has no endpoints; the bulk pair is on 1
        _check(_lib.libusb_set_interface_alt_setting(self.h, IFACE, 1), "interface 5 alt 1")

    def write(self, data: bytes, timeout_ms=1000):
        n = C.c_int()
        buf = C.create_string_buffer(data, len(data))
        _check(_lib.libusb_bulk_transfer(self.h, EP_OUT, buf, len(data), C.byref(n), timeout_ms), "bulk out")
        return n.value

    def read(self, size=1024, timeout_ms=1000) -> bytes:
        n = C.c_int()
        buf = C.create_string_buffer(size)
        _check(_lib.libusb_bulk_transfer(self.h, EP_IN, buf, size, C.byref(n), timeout_ms), "bulk in")
        return buf.raw[: n.value]

    def close(self):
        if self.h:
            _lib.libusb_release_interface(self.h, IFACE)
            _lib.libusb_close(self.h)
            self.h = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
