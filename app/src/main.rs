//! io44-control as an app: the page in its own window (WebView2 on Windows, WebKitGTK on Linux) and an icon in the
//! system tray. The controller is still the Python package (`io44/`): this program starts its page's server
//! (`python -m io44 ui --no-browser`) and stops it again on Quit. When a server is already there (the Linux user
//! service, say) it is used as it is and left running.
//!
//! Closing the window leaves everything running in the tray (the io44 still gets its settings when it is plugged in).
//! `--hidden` starts in the tray only (start with the computer). A second start shows the first one's window.
//!
//! Where the Python package is: `IO44_HOME`, else the folder of this program or one above it holding `io44/`.
//! Which Python: Windows `py\pythonw.exe` there (the Windows package), else `pythonw`; Linux `python3`.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{Read, Write};
use std::net::TcpStream;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use tauri::menu::{CheckMenuItem, Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{AppHandle, Manager, WebviewUrl, WebviewWindowBuilder, WindowEvent};

const PORT: u16 = 8794;

// ---- the page's server -------------------------------------------------------------------------------------------

/// One HTTP request to the page's server; the body of a 200 answer
fn http(method: &str, path: &str, body: Option<&str>) -> Option<String> {
    let mut c = TcpStream::connect_timeout(&([127, 0, 0, 1], PORT).into(), Duration::from_millis(500)).ok()?;
    c.set_read_timeout(Some(Duration::from_secs(10))).ok()?;
    let b = body.unwrap_or("");
    let head = if body.is_some() { format!("Content-Type: application/json\r\nContent-Length: {}\r\n", b.len()) } else { String::new() };
    write!(c, "{method} {path} HTTP/1.1\r\nHost: 127.0.0.1\r\n{head}Connection: close\r\n\r\n{b}").ok()?;
    let mut out = Vec::new();
    c.read_to_end(&mut out).ok()?;
    let s = String::from_utf8_lossy(&out).into_owned();
    let (status, rest) = s.split_once("\r\n")?;
    if !status.contains(" 200 ") {
        return None;
    }
    Some(rest.split_once("\r\n\r\n")?.1.to_string())
}

/// The page's state when an io44-control server answers on the port
fn server_state() -> Option<serde_json::Value> {
    let v: serde_json::Value = serde_json::from_str(&http("GET", "/api/state", None)?).ok()?;
    v.get("buses").is_some().then_some(v)
}

fn port_taken() -> bool {
    TcpStream::connect_timeout(&([127, 0, 0, 1], PORT).into(), Duration::from_millis(300)).is_ok()
}

/// The folder holding the `io44` package
fn home() -> Option<PathBuf> {
    let ok = |d: &Path| d.join("io44").join("__init__.py").is_file();
    if let Some(d) = std::env::var_os("IO44_HOME").map(PathBuf::from) {
        return ok(&d).then_some(d);
    }
    let exe = std::env::current_exe().ok()?;
    exe.ancestors().skip(1).take(6).find(|d| ok(d)).map(Path::to_path_buf)
}

/// Where the server's output goes (beside the settings)
fn log_path() -> Option<PathBuf> {
    let base = if cfg!(windows) {
        std::env::var_os("APPDATA").map(PathBuf::from)
    } else {
        std::env::var_os("XDG_CONFIG_HOME").map(PathBuf::from).or_else(|| std::env::var_os("HOME").map(|h| PathBuf::from(h).join(".config")))
    }?;
    let d = base.join("io44-control");
    std::fs::create_dir_all(&d).ok()?;
    Some(d.join("app-server.log"))
}

fn spawn_server(home: &Path) -> std::io::Result<Child> {
    let python = if cfg!(windows) {
        let p = home.join("py").join("pythonw.exe");
        if p.is_file() { p } else { PathBuf::from("pythonw") }
    } else {
        PathBuf::from("python3")
    };
    let mut cmd = Command::new(python);
    cmd.args(["-m", "io44", "ui", "--no-browser", "--port", &PORT.to_string()]).current_dir(home).stdin(Stdio::null());
    match log_path().and_then(|p| std::fs::OpenOptions::new().create(true).append(true).open(p).ok()) {
        Some(f) => {
            let f2 = f.try_clone()?;
            cmd.stdout(f).stderr(f2);
        }
        None => {
            cmd.stdout(Stdio::null()).stderr(Stdio::null());
        }
    }
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        cmd.creation_flags(0x0800_0000); // CREATE_NO_WINDOW
    }
    cmd.spawn()
}

/// The server this program started (None: it was already running, or is not up)
struct Server {
    home: Option<PathBuf>,
    child: Option<Child>,
    restarts: u32,
}

impl Server {
    /// Make sure a server answers: use one that is there, else start ours and wait for it (up to 15 s)
    fn ensure(&mut self) -> Result<(), String> {
        if server_state().is_some() {
            return Ok(());
        }
        if let Some(c) = self.child.as_mut() {
            if c.try_wait().ok().flatten().is_none() {
                return Ok(()); // still starting
            }
            self.child = None;
        }
        if port_taken() {
            return Err(format!("port {PORT} is used by another program"));
        }
        let home = self.home.clone().ok_or("the io44 package was not found beside the program (or set IO44_HOME)")?;
        self.child = Some(spawn_server(&home).map_err(|e| format!("could not start Python: {e}"))?);
        let t = Instant::now();
        while t.elapsed() < Duration::from_secs(15) {
            if server_state().is_some() {
                return Ok(());
            }
            if let Some(Ok(Some(st))) = self.child.as_mut().map(|c| c.try_wait()) {
                self.child = None;
                return Err(format!("the server stopped at once ({st}); see app-server.log"));
            }
            std::thread::sleep(Duration::from_millis(150));
        }
        Err("the server did not answer".into())
    }

    fn stop(&mut self) {
        if let Some(mut c) = self.child.take() {
            let _ = c.kill();
            let _ = c.wait();
        }
    }
}

// ---- start with the computer, Universal Control's service (Windows) ---------------------------------------------

#[cfg(windows)]
mod sys {
    use std::os::windows::process::CommandExt;
    use std::process::Command;

    const RUN: &str = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run";
    const SERVICE: &str = "PreSonus Hardware Access Service";

    fn quiet(c: &mut Command) -> &mut Command {
        c.creation_flags(0x0800_0000)
    }

    pub fn autostart() -> bool {
        quiet(Command::new("reg").args(["query", RUN, "/v", "io44-control"])).output().map(|o| o.status.success()).unwrap_or(false)
    }

    pub fn set_autostart(on: bool) {
        if on {
            let exe = std::env::current_exe().map(|p| p.display().to_string()).unwrap_or_default();
            let _ = quiet(Command::new("reg").args(["add", RUN, "/v", "io44-control", "/t", "REG_SZ", "/d", &format!("\"{exe}\" --hidden"), "/f"])).status();
        } else {
            let _ = quiet(Command::new("reg").args(["delete", RUN, "/v", "io44-control", "/f"])).status();
        }
    }

    /// The tray of the earlier Windows package started from a shortcut in the Startup folder: the app takes over
    pub fn take_over_old_startup() {
        let Some(a) = std::env::var_os("APPDATA") else { return };
        let lnk = std::path::PathBuf::from(a).join(r"Microsoft\Windows\Start Menu\Programs\Startup\io44-control.lnk");
        if lnk.is_file() && std::fs::remove_file(&lnk).is_ok() {
            set_autostart(true);
        }
    }

    /// "running", "stopped" or "none"
    pub fn uc_state() -> &'static str {
        match quiet(Command::new("sc").args(["query", SERVICE])).output() {
            Ok(o) if o.status.success() => {
                if String::from_utf8_lossy(&o.stdout).contains("RUNNING") { "running" } else { "stopped" }
            }
            _ => "none",
        }
    }

    fn b64(data: &[u8]) -> String {
        const T: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        let mut s = String::new();
        for c in data.chunks(3) {
            let n = (c[0] as u32) << 16 | (*c.get(1).unwrap_or(&0) as u32) << 8 | *c.get(2).unwrap_or(&0) as u32;
            for i in 0..4 {
                s.push(if i <= c.len() { T[(n >> (18 - 6 * i) & 63) as usize] as char } else { '=' });
            }
        }
        s
    }

    /// Universal Control's service stopped and disabled, or set to start with Windows and started (asks for an
    /// administrator)
    pub fn uc_set(stop: bool) {
        let cmd = if stop {
            format!("Stop-Service -Name '{SERVICE}' -Force; Set-Service -Name '{SERVICE}' -StartupType Disabled")
        } else {
            format!("Set-Service -Name '{SERVICE}' -StartupType Automatic; Start-Service -Name '{SERVICE}'")
        };
        let enc = b64(&cmd.encode_utf16().flat_map(|u| u.to_le_bytes()).collect::<Vec<u8>>());
        let outer = format!("Start-Process powershell -Verb RunAs -WindowStyle Hidden -ArgumentList '-NoProfile -WindowStyle Hidden -EncodedCommand {enc}'");
        let _ = quiet(Command::new("powershell").args(["-NoProfile", "-WindowStyle", "Hidden", "-Command", &outer])).spawn();
    }
}

#[cfg(not(windows))]
mod sys {
    use std::path::PathBuf;

    fn desktop() -> Option<PathBuf> {
        let base = std::env::var_os("XDG_CONFIG_HOME").map(PathBuf::from).or_else(|| std::env::var_os("HOME").map(|h| PathBuf::from(h).join(".config")))?;
        Some(base.join("autostart").join("io44-control.desktop"))
    }

    pub fn autostart() -> bool {
        desktop().is_some_and(|p| p.is_file())
    }

    pub fn set_autostart(on: bool) {
        let Some(p) = desktop() else { return };
        if on {
            let exe = std::env::current_exe().map(|p| p.display().to_string()).unwrap_or_default();
            let _ = std::fs::create_dir_all(p.parent().unwrap());
            let _ = std::fs::write(&p, format!("[Desktop Entry]\nType=Application\nName=io44-control\nComment=Revelator io44 control\nExec=\"{exe}\" --hidden\nTerminal=false\nX-GNOME-Autostart-enabled=true\n"));
        } else {
            let _ = std::fs::remove_file(p);
        }
    }

    pub fn take_over_old_startup() {}

    pub fn uc_state() -> &'static str {
        "none"
    }

    pub fn uc_set(_stop: bool) {}
}

// ---- the window and the tray ---------------------------------------------------------------------------------------

fn show(app: &AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }
}

struct Words {
    open: &'static str,
    apply: &'static str,
    repair: &'static str,
    autostart: &'static str,
    uc_stop: &'static str,
    uc_start: &'static str,
    quit: &'static str,
    tip_ok: &'static str,
    tip_off: &'static str,
    tip_uc: &'static str,
    tip_err: &'static str,
}

fn words() -> Words {
    let zh = sys_locale::get_locale().is_some_and(|l| l.to_lowercase().starts_with("zh"));
    if zh {
        Words {
            open: "開啟 io44-control",
            apply: "立即寫入設定",
            repair: "修復混音靜音（重新初始化 io44）",
            autostart: "開機時自動啟動",
            uc_stop: "停用 Universal Control 的服務…",
            uc_start: "恢復 Universal Control 的服務…",
            quit: "結束 io44-control",
            tip_ok: "io44-control：已連上 io44",
            tip_off: "io44-control：沒有連上 io44",
            tip_uc: "io44-control：io44 被 Universal Control 佔用",
            tip_err: "io44-control：控制程式沒有執行",
        }
    } else {
        Words {
            open: "Open io44-control",
            apply: "Write the settings now",
            repair: "Repair silent mixes (restart the io44)",
            autostart: "Start with the computer",
            uc_stop: "Stop Universal Control's service…",
            uc_start: "Bring back Universal Control's service…",
            quit: "Quit io44-control",
            tip_ok: "io44-control: the io44 is connected",
            tip_off: "io44-control: no io44",
            tip_uc: "io44-control: Universal Control has the io44",
            tip_err: "io44-control: the controller is not running",
        }
    }
}

/// A page shown when the server could not be started
fn error_page(msg: &str) -> String {
    let m: String = msg.chars().map(|c| if c.is_ascii_alphanumeric() || c == ' ' { c.to_string() } else { format!("%{:02X}", c as u32 & 0xff) }).collect();
    format!("data:text/html;charset=utf-8,<body style='background:%23181a1f;color:%23ddd;font-family:sans-serif;padding:2em'><h3>io44-control</h3><p>{m}</p></body>")
}

fn main() {
    // WebKitGTK's DMA-BUF renderer leaves the window blank with NVIDIA's driver: use the other path there
    #[cfg(not(windows))]
    if Path::new("/proc/driver/nvidia").exists() && std::env::var_os("WEBKIT_DISABLE_DMABUF_RENDERER").is_none() {
        std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");
    }
    let hidden = std::env::args().any(|a| a == "--hidden");
    let server = Arc::new(Mutex::new(Server { home: home(), child: None, restarts: 0 }));
    let started = server.lock().unwrap().ensure();
    let w = words();

    let s_exit = server.clone();
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| show(app)))
        .setup(move |app| {
            let url = match &started {
                Ok(()) => WebviewUrl::External(format!("http://127.0.0.1:{PORT}/").parse()?),
                Err(e) => WebviewUrl::External(error_page(e).parse()?),
            };
            WebviewWindowBuilder::new(app, "main", url)
                .title("io44-control")
                .inner_size(1220.0, 900.0)
                .min_inner_size(360.0, 440.0)
                .visible(false)
                .build()?;
            // shown once built (WebKitGTK under Cinnamon left a window built visible unmapped)
            if !hidden || started.is_err() {
                show(app.handle());
            }

            sys::take_over_old_startup();
            let open = MenuItem::with_id(app, "open", w.open, true, None::<&str>)?;
            let apply = MenuItem::with_id(app, "apply", w.apply, true, None::<&str>)?;
            let repair = MenuItem::with_id(app, "repair", w.repair, true, None::<&str>)?;
            let auto = CheckMenuItem::with_id(app, "auto", w.autostart, true, sys::autostart(), None::<&str>)?;
            let uc = MenuItem::with_id(app, "uc", w.uc_stop, true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", w.quit, true, None::<&str>)?;
            let (sep1, sep2) = (PredefinedMenuItem::separator(app)?, PredefinedMenuItem::separator(app)?);
            let menu = if cfg!(windows) {
                // the io44 is put back through its sample rate on Linux only (Windows: the driver's own)
                Menu::with_items(app, &[&open, &apply, &auto, &sep1, &uc, &sep2, &quit])?
            } else {
                Menu::with_items(app, &[&open, &apply, &repair, &auto, &sep1, &quit])?
            };
            let auto2 = auto.clone();
            let mut tray = TrayIconBuilder::with_id("tray")
                .tooltip("io44-control")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(move |app, e| match e.id().as_ref() {
                    "open" => show(app),
                    "apply" => {
                        std::thread::spawn(|| http("POST", "/api/apply", Some("{}")));
                    }
                    "repair" => {
                        std::thread::spawn(|| http("POST", "/api/repair", Some("{}")));
                    }
                    "auto" => {
                        sys::set_autostart(!sys::autostart());
                        let _ = auto2.set_checked(sys::autostart());
                    }
                    "uc" => match sys::uc_state() {
                        "running" => sys::uc_set(true),
                        "stopped" => sys::uc_set(false),
                        _ => {}
                    },
                    "quit" => app.exit(0),
                    _ => {}
                })
                // a left click opens the window (Windows; Linux tray icons only have the menu)
                .on_tray_icon_event(|tray, e| {
                    if let TrayIconEvent::Click { button: MouseButton::Left, button_state: MouseButtonState::Up, .. } = e {
                        show(tray.app_handle());
                    }
                });
            if let Some(icon) = app.default_window_icon() {
                tray = tray.icon(icon.clone());
            }
            let tray = tray.build(app)?;

            // every two seconds: is the io44 there, is Universal Control's service running; and the server still
            // up (started again when it stopped on its own, a few times)
            let (s, h) = (server.clone(), app.handle().clone());
            std::thread::spawn(move || {
                let mut last_tip = String::new();
                let mut last_uc = "";
                loop {
                    std::thread::sleep(Duration::from_secs(2));
                    let st = server_state();
                    if st.is_none() {
                        let mut g = s.lock().unwrap();
                        if g.restarts < 5 && g.ensure().is_ok() {
                            g.restarts += 1;
                            let h2 = h.clone();
                            let _ = h.run_on_main_thread(move || {
                                if let Some(w) = h2.get_webview_window("main") {
                                    let _ = w.eval("location.reload()");
                                }
                            });
                        }
                    }
                    let ucs = sys::uc_state();
                    let connected = st.as_ref().and_then(|v| v.get("connected")).and_then(|c| c.as_bool()).unwrap_or(false);
                    let tip = if st.is_none() {
                        w.tip_err
                    } else if connected {
                        w.tip_ok
                    } else if ucs == "running" {
                        w.tip_uc
                    } else {
                        w.tip_off
                    };
                    if tip != last_tip {
                        last_tip = tip.to_string();
                        let _ = tray.set_tooltip(Some(tip));
                    }
                    if ucs != last_uc {
                        last_uc = ucs;
                        let _ = uc.set_text(if ucs == "running" { w.uc_stop } else { w.uc_start });
                        let _ = uc.set_enabled(ucs != "none");
                    }
                }
            });
            Ok(())
        })
        .on_window_event(|w, e| {
            // closing the window keeps the controller running in the tray
            if let WindowEvent::CloseRequested { api, .. } = e {
                api.prevent_close();
                let _ = w.hide();
            }
        })
        .build(tauri::generate_context!())
        .expect("the app window did not start")
        .run(move |_app, e| {
            if let tauri::RunEvent::Exit = e {
                s_exit.lock().unwrap().stop();
            }
        });
}
