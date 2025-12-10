@echo off
REM Launch Spotify Overlay without console window
REM This uses pythonw.exe instead of python.exe to hide the console

start "" pythonw.exe "%~dp0spotify_milkdrop_overlay.py"
