#!/usr/bin/env bash
# One-click launcher for the Plain Language GUI (macOS / Linux).
# Double-click in a file manager, or run: bash run_gui.sh
set -e
cd "$(dirname "$0")"
echo "Setting up (first run may take a minute)..."
pip install -q -r requirements-gui.txt
echo "Starting Plain Language — your browser will open shortly."
python -m src.gui
