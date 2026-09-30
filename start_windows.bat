@echo off
cd /d "%~dp0"
if not exist .venv py -3.12 -m venv .venv
if errorlevel 1 exit /b 1
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
.venv\Scripts\python server.py
