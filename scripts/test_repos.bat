@echo off
rem Демонстрация работы с тестовыми репозиториями (режим test).
setlocal
cd /d "%~dp0.."
set RUN="%CD%\run.bat"
chcp 65001 >nul
set REPOS=tests\repos

echo --- общая зависимость (ромб) ---
call :run -p A -r %REPOS%\simple.txt -m test
call :run -p B -r %REPOS%\simple.txt -m test

echo --- максимальная глубина ---
call :run -p A -r %REPOS%\chain.txt -m test -d 1
call :run -p A -r %REPOS%\chain.txt -m test -d 3
call :run -p A -r %REPOS%\chain.txt -m test -d 10

echo --- циклические зависимости ---
call :run -p A -r %REPOS%\cycle.txt -m test -d 5
call :run -p A -r %REPOS%\cycle.txt -m test -d 2
call :run -p A -r %REPOS%\self_cycle.txt -m test
call :run -p A -r %REPOS%\complex.txt -m test -d 10
exit /b 0

:run
echo ^> run.bat %*
call %RUN% %*
echo exit code: %ERRORLEVEL%
echo.
exit /b 0
