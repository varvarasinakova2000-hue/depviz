@echo off
set PY=python
where py >nul 2>nul && set PY=py
%PY% "%~dp0src\main.py" %*
