"""io44-control in the Windows notification area (next to the clock): the page's server running in the background
(the io44 written whenever it is plugged in, the front panel's blend followed), a menu to open the page, write the
settings again, start with Windows, and stop or bring back Universal Control's service (only one program can hold the
io44's control interface). Win32 through ctypes, nothing to install.

  pythonw -m io44 tray
"""
import ctypes
import json
import os
import subprocess
import sys
import threading
import urllib.request
from ctypes import wintypes as W

PORT = 8794
URL = f"http://127.0.0.1:{PORT}/"
SERVICE = "PreSonus Hardware Access Service"
STARTUP = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup", "io44-control.lnk")

u32, s32, k32 = ctypes.windll.user32, ctypes.windll.shell32, ctypes.windll.kernel32
LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
u32.DefWindowProcW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
u32.DefWindowProcW.restype = LRESULT
u32.CreateWindowExW.restype = W.HWND
u32.CreateWindowExW.argtypes = [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, W.HWND, W.HMENU, W.HINSTANCE, W.LPVOID]
u32.LoadIconW.restype = W.HICON
u32.LoadImageW.restype = W.HANDLE
u32.CreatePopupMenu.restype = W.HMENU
u32.TrackPopupMenu.argtypes = [W.HMENU, W.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, W.HWND, W.LPVOID]
u32.AppendMenuW.argtypes = [W.HMENU, W.UINT, ctypes.c_size_t, W.LPCWSTR]
s32.ShellExecuteW.argtypes = [W.HWND, W.LPCWSTR, W.LPCWSTR, W.LPCWSTR, W.LPCWSTR, ctypes.c_int]

WM_DESTROY, WM_COMMAND, WM_TIMER, WM_USER = 0x0002, 0x0111, 0x0113, 0x0400
WM_LBUTTONDBLCLK, WM_RBUTTONUP, WM_LBUTTONUP = 0x0203, 0x0205, 0x0202
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP, NIF_INFO = 1, 2, 4, 0x10
MF_STRING, MF_SEPARATOR, MF_CHECKED, MF_GRAYED = 0, 0x800, 0x8, 0x1
TPM_RETURNCMD, TPM_RIGHTBUTTON = 0x100, 0x2
CALLBACK = WM_USER + 1


class GUID(ctypes.Structure):
    _fields_ = [("a", W.DWORD), ("b", W.WORD), ("c", W.WORD), ("d", ctypes.c_ubyte * 8)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [("cbSize", W.DWORD), ("hWnd", W.HWND), ("uID", W.UINT), ("uFlags", W.UINT),
                ("uCallbackMessage", W.UINT), ("hIcon", W.HICON), ("szTip", W.WCHAR * 128), ("dwState", W.DWORD),
                ("dwStateMask", W.DWORD), ("szInfo", W.WCHAR * 256), ("uVersion", W.UINT),
                ("szInfoTitle", W.WCHAR * 64), ("dwInfoFlags", W.DWORD), ("guidItem", GUID), ("hBalloonIcon", W.HICON)]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", W.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                ("hInstance", W.HINSTANCE), ("hIcon", W.HICON), ("hCursor", W.HANDLE), ("hbrBackground", W.HBRUSH),
                ("lpszMenuName", W.LPCWSTR), ("lpszClassName", W.LPCWSTR)]


ZH = {"open": "開啟控制頁面", "apply": "立即寫入設定", "startup": "開機時自動啟動", "quit": "結束 io44-control",
      "repair": "修復混音靜音（重新初始化 io44）", "uc_stop": "停用 Universal Control 的服務…", "uc_start": "恢復 Universal Control 的服務…",
      "tip_ok": "io44-control：已連上 io44", "tip_off": "io44-control：沒有連上 io44",
      "tip_uc": "io44-control：io44 被 Universal Control 佔用",
      "uc_title": "Universal Control 正在使用 io44",
      "uc_body": "一次只能有一個程式控制 io44。要改用 io44-control，請在這個圖示的選單停用 Universal Control 的服務。"}


def service_state() -> str:
    """'running', 'stopped' or 'none' (Universal Control's service)"""
    r = subprocess.run(["sc", "query", SERVICE], capture_output=True, text=True, creationflags=0x08000000)
    if r.returncode != 0:
        return "none"
    return "running" if "RUNNING" in r.stdout else "stopped"


def service_set(stop: bool):
    """Universal Control's service stopped and disabled, or set to start with Windows and started (asks for an
    administrator)"""
    cmd = (f"Stop-Service -Name '{SERVICE}' -Force; Set-Service -Name '{SERVICE}' -StartupType Disabled" if stop else
           f"Set-Service -Name '{SERVICE}' -StartupType Automatic; Start-Service -Name '{SERVICE}'")
    s32.ShellExecuteW(None, "runas", "powershell.exe", f'-NoProfile -WindowStyle Hidden -Command "{cmd}"', None, 0)


def startup_set(on: bool):
    """a shortcut in the user's Startup folder (pythonw -m io44 tray in this folder)"""
    if not on:
        if os.path.exists(STARTUP):
            os.remove(STARTUP)
        return
    exe = sys.executable.replace("python.exe", "pythonw.exe")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{STARTUP}'); $s.TargetPath='{exe}'; "
          f"$s.Arguments='-m io44 tray'; $s.WorkingDirectory='{here}'; $s.Description='io44-control'; $s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], creationflags=0x08000000)


def api(path, body=None):
    req = urllib.request.Request(URL.rstrip("/") + path, json.dumps(body).encode() if body is not None else None,
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def run(start_server):
    """start_server(): runs the page's server (blocking); it goes on a thread, the tray on this one"""
    threading.Thread(target=start_server, daemon=True, name="server").start()
    hinst = k32.GetModuleHandleW(None)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "icon.ico")
    hicon = u32.LoadImageW(None, icon_path, 1, 0, 0, 0x10 | 0x40) if os.path.exists(icon_path) else None
    hicon = hicon or u32.LoadIconW(None, ctypes.c_void_p(32512))  # IDI_APPLICATION
    nid = NOTIFYICONDATAW()
    nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
    state = {"warned": False}

    def tip(text, info=None):
        nid.szTip = text[:127]
        nid.uFlags = NIF_TIP
        if info:
            nid.uFlags |= NIF_INFO
            nid.szInfoTitle, nid.szInfo = info[0][:63], info[1][:255]
            nid.dwInfoFlags = 2  # a warning
        s32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    def refresh():
        uc = service_state() == "running"
        try:
            ok = api("/api/state").get("connected")
        except Exception:
            ok = False
        if uc and not ok:
            tip(ZH["tip_uc"], None if state["warned"] else (ZH["uc_title"], ZH["uc_body"]))
            state["warned"] = True
        else:
            tip(ZH["tip_ok"] if ok else ZH["tip_off"])

    def menu(hwnd):
        m = u32.CreatePopupMenu()
        uc = service_state()
        u32.AppendMenuW(m, MF_STRING, 1, ZH["open"])
        u32.AppendMenuW(m, MF_STRING, 2, ZH["apply"])
        u32.AppendMenuW(m, MF_STRING, 6, ZH["repair"])
        u32.AppendMenuW(m, MF_STRING | (MF_CHECKED if os.path.exists(STARTUP) else 0), 3, ZH["startup"])
        u32.AppendMenuW(m, MF_SEPARATOR, 0, None)
        if uc == "running":
            u32.AppendMenuW(m, MF_STRING, 4, ZH["uc_stop"])
        elif uc == "stopped":
            u32.AppendMenuW(m, MF_STRING, 5, ZH["uc_start"])
        u32.AppendMenuW(m, MF_SEPARATOR, 0, None)
        u32.AppendMenuW(m, MF_STRING, 9, ZH["quit"])
        pt = W.POINT()
        u32.GetCursorPos(ctypes.byref(pt))
        u32.SetForegroundWindow(hwnd)
        cmd = u32.TrackPopupMenu(m, TPM_RETURNCMD | TPM_RIGHTBUTTON, pt.x, pt.y, 0, hwnd, None)
        u32.DestroyMenu(m)
        if cmd == 1:
            os.startfile(URL)
        elif cmd == 2:
            try:
                api("/api/apply", {})
            except Exception:
                pass
            refresh()
        elif cmd == 3:
            startup_set(not os.path.exists(STARTUP))
        elif cmd == 6:
            try:
                api("/api/repair", {})
            except Exception:
                pass
            refresh()
        elif cmd == 4:
            service_set(True)
        elif cmd == 5:
            service_set(False)
        elif cmd == 9:
            u32.DestroyWindow(hwnd)

    @WNDPROC
    def proc(hwnd, msg, wp, lp):
        if msg == CALLBACK:
            if lp == WM_RBUTTONUP:
                menu(hwnd)
            elif lp in (WM_LBUTTONDBLCLK, WM_LBUTTONUP):
                os.startfile(URL)
            return 0
        if msg == WM_TIMER:
            refresh()
            return 0
        if msg == WM_DESTROY:
            s32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
            u32.PostQuitMessage(0)
            return 0
        return u32.DefWindowProcW(hwnd, msg, wp, lp)

    wc = WNDCLASSW(lpfnWndProc=proc, hInstance=hinst, lpszClassName="io44-control-tray")
    u32.RegisterClassW(ctypes.byref(wc))
    hwnd = u32.CreateWindowExW(0, "io44-control-tray", "io44-control", 0, 0, 0, 0, 0, None, None, hinst, None)
    nid.hWnd, nid.uID, nid.uFlags, nid.uCallbackMessage, nid.hIcon = hwnd, 1, NIF_MESSAGE | NIF_ICON | NIF_TIP, CALLBACK, hicon
    nid.szTip = "io44-control"
    s32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
    u32.SetTimer(hwnd, 1, 2000, None)
    msg = W.MSG()
    while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        u32.TranslateMessage(ctypes.byref(msg))
        u32.DispatchMessageW(ctypes.byref(msg))
    os._exit(0)
