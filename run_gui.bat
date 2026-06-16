@echo off
REM One-click launcher for the Plain Language GUI (Windows).
REM Double-click this file, or run: run_gui.bat
cd /d "%~dp0"
echo Setting up (first run may take a minute)...
pip install -q -r requirements-gui.txt
echo Starting Plain Language - your browser will open shortly.
python -m src.gui
