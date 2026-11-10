#!/bin/sh
# Run on the build machine from the repo root: the Linux app inside the Ubuntu 24.04 image.
# Output: app/target-u2404/release/io44-control. The cargo registry is cached in ~/.cache/io44-control-cargo.
set -e
podman image exists io44-control-build || podman build -t io44-control-build app/build/
mkdir -p "$HOME/.cache/io44-control-cargo"
podman run --rm -v "$PWD:/src" -v "$HOME/.cache/io44-control-cargo:/opt/cargo/registry" \
  -e CARGO_TARGET_DIR=/src/app/target-u2404 io44-control-build cargo build --release --manifest-path app/Cargo.toml "$@"
