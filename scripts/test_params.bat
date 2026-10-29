@echo off
rem Демонстрация запуска с корректными параметрами.
setlocal
cd /d "%~dp0.."
set RUN="%CD%\run.bat"
chcp 65001 >nul

call :run -p requests -r https://pypi.org/pypi -v 2.31.0
call :run --package flask --repo https://pypi.org/pypi --mode remote ^
    --version 3.0.0 --output flask.svg --max-depth 5
call :run -p requests -r https://pypi.org/pypi -v latest
call :run -p A -r tests\repos\simple.txt -m test -d 2 -o test_graph.svg
exit /b 0

:run
echo ^> run.bat %*
call %RUN% %*
echo exit code: %ERRORLEVEL%
echo.
exit /b 0
