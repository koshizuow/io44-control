#!/bin/sh
# Run on the build machine from the repo root (Rust with the x86_64-pc-windows-gnu target and mingw-w64):
# Output: app/target/x86_64-pc-windows-gnu/release/io44-control.exe and WebView2Loader.dll beside it.
set -e
cargo build --release --target x86_64-pc-windows-gnu --manifest-path app/Cargo.toml "$@"
