#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="${DIST_DIR:-$ROOT_DIR/dist}"

cd "$ROOT_DIR"

echo "==> Building python3-lilv debian package..."
./build-python3-lilv.sh

echo "==> Building wheel..."
mkdir -p "$DIST_DIR"
pip3 install --upgrade pip
pip3 wheel --no-deps -w "$DIST_DIR" .

echo "==> Copying debian package to $DIST_DIR..."
cp python3-lilv_*.deb "$DIST_DIR/"

echo "==> Build complete. Artifacts in $DIST_DIR:"
ls -la "$DIST_DIR"
