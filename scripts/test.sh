#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="${DIST_DIR:-$ROOT_DIR/dist}"
VENV_DIR="${VENV_DIR:-/tmp/test-venv}"

echo "==> Creating virtual environment..."
python3 -m venv --system-site-packages "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip

echo "==> Installing debian package..."
dpkg -i "$DIST_DIR"/python3-lilv_*.deb

echo "==> Installing wheel..."
pip install "$DIST_DIR"/mod_lilvlib-*.whl

echo "==> Testing imports..."
python -c "import lilv; print('lilv import OK')"
python -c "import lilvlib; print('lilvlib import OK, version:', lilvlib.__version__)"

echo "==> Testing CLI..."
which lilvlib

echo "==> Running test script..."
cd "$ROOT_DIR"
python test.py

echo "==> Running pylint..."
pip install pylint
pylint -E lilvlib/lilvlib.py

echo "==> All tests passed"
