#!/bin/sh
PY=python3
command -v python3 >/dev/null 2>&1 || PY=python
cd "$(dirname "$0")" && "$PY" src/main.py "$@"
