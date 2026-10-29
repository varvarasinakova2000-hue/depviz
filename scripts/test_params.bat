@echo off
rem Демонстрация построения графа зависимостей пакетов из PyPI.
setlocal
cd /d "%~dp0.."
set RUN="%CD%\run.bat"
chcp 65001 >nul
set URL=https://pypi.org/pypi

call :run -p requests -r %URL% -v 2.31.0
call :run --package flask --repo %URL% --mode remote ^
    --version 3.0.0 --output flask.svg --max-depth 2
call :run -p flask -r %URL% -v 3.0.0 -d 1
call :run -p six -r %URL% -v 1.16.0
exit /b 0

:run
echo ^> run.bat %*
call %RUN% %*
echo exit code: %ERRORLEVEL%
echo.
exit /b 0
