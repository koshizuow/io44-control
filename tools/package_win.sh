#!/bin/sh
# Pack io44-control for Windows into dist/io44-control-DATE-windows.zip: the app (io44-control.exe, the page in a
# window with a tray icon, and WebView2Loader.dll), the io44 package, Python's embeddable distribution (py\, its path
# file reaching the folder above), libusb's DLL and the instructions.
# Run from the repo root on the build machine, after app/build/windows.sh (cargo and its registry are needed for the
# Rust crates' licenses), on a machine that may download (the files are kept in $CACHE and checked against hashes).
set -e
CACHE=${CACHE:-$HOME/dl/io44win}
PY=python-3.12.10-embed-amd64.zip
PY_SHA=4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3
LU=libusb-1.0.27.7z
LU_SHA=19835e290f46fab6bd8ce4be6ab7dc5209f1c04bad177065df485e51dc4118c8
LC=libusb-COPYING
LC_SHA=5df07007198989c622f5d41de8d703e7bef3d0e79d62e24332ee739a452af62a
mkdir -p "$CACHE" dist
[ -f "$CACHE/$PY" ] || curl -sSL -o "$CACHE/$PY" https://www.python.org/ftp/python/3.12.10/$PY
[ -f "$CACHE/$LU" ] || curl -sSL -o "$CACHE/$LU" https://github.com/libusb/libusb/releases/download/v1.0.27/$LU
echo "$PY_SHA  $CACHE/$PY" | sha256sum -c -
[ -f "$CACHE/$LC" ] || curl -sSL -o "$CACHE/$LC" https://raw.githubusercontent.com/libusb/libusb/v1.0.27/COPYING
echo "$LU_SHA  $CACHE/$LU" | sha256sum -c -
echo "$LC_SHA  $CACHE/$LC" | sha256sum -c -
STAMP=$(date +%Y%m%d)
APP=${APP:-app/target/x86_64-pc-windows-gnu/release}
for f in "$APP/io44-control.exe" "$APP/WebView2Loader.dll"; do [ -f "$f" ] || { echo "missing $f: run app/build/windows.sh"; exit 1; }; done
T=$(mktemp -d); D="$T/io44-control"
mkdir -p "$D/py" "$T/lu"
unzip -q "$CACHE/$PY" -d "$D/py"
# the folder above py\ on the path: io44 is found from anywhere
printf 'python312.zip\n.\n..\n' > "$D/py/python312._pth"
7z x -y -o"$T/lu" "$CACHE/$LU" >/dev/null
cp "$T/lu/VS2022/MS64/dll/libusb-1.0.dll" "$D/"
mkdir -p "$D/licenses"
cp LICENSE "$D/licenses/io44-control-LICENSE.txt"
python3 tools/third_party.py app/Cargo.toml "$D/licenses/THIRD_PARTY_LICENSES.txt" x86_64-pc-windows-gnu
cp "$APP/io44-control.exe" "$APP/WebView2Loader.dll" "$D/"
cp "$CACHE/$LC" "$D/licenses/libusb-COPYING.txt"
cp "$D/py/LICENSE.txt" "$D/licenses/python-LICENSE.txt" 2>/dev/null || true
printf 'libusb 1.0.27 (LGPL-2.1), unmodified: https://github.com/libusb/libusb/releases/tag/v1.0.27\r\nPython 3.12.10 embeddable (PSF License): https://www.python.org/downloads/release/python-31210/\r\nio44-control.exe: GPL-3.0-or-later (io44-control-LICENSE.txt); the Rust crates built into it, WebView2Loader.dll among them: THIRD_PARTY_LICENSES.txt\r\n' > "$D/licenses/README.txt"
cp -r io44 "$D/io44"
find "$D/io44" -name __pycache__ -prune -exec rm -rf {} +
# the instructions: UTF-8 with a BOM and CRLF (Notepad on older Windows)
printf '\357\273\277' > "$D/使用說明.txt"
sed 's/$/\r/' tools/windows-readme.txt >> "$D/使用說明.txt"
(cd "$T" && zip -qr9 "$OLDPWD/dist/io44-control-$STAMP-windows.zip" io44-control)
rm -rf "$T"
ls -la "dist/io44-control-$STAMP-windows.zip"
