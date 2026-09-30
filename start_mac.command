#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null; then echo 'Install Python 3.12 from python.org first.'; exit 1; fi
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
if [ ! -d .venv ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python server.py
