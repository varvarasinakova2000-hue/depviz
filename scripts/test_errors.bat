@echo off
rem Демонстрация обработки ошибок для всех параметров.
setlocal
cd /d "%~dp0.."
set RUN="%CD%\run.bat"
chcp 65001 >nul
set URL=https://pypi.org/pypi
set REPO=tests\repos\simple.txt

echo --- обязательные параметры ---
call :run -r %URL% -v 2.31.0
call :run -p requests -v 2.31.0

echo --- имя пакета ---
call :run -p "" -r %URL% -v 2.31.0
call :run -p "bad name" -r %URL% -v 2.31.0
call :run -p a -r %REPO% -m test

echo --- репозиторий ---
call :run -p requests -r pypi.org -v 2.31.0
call :run -p requests -r ftp://pypi.org/pypi -v 2.31.0
call :run -p A -r missing.txt -m test
call :run -p A -r tests -m test

echo --- режим ---
call :run -p A -r %REPO% -m local

echo --- версия ---
call :run -p requests -r %URL%
call :run -p requests -r %URL% -v v1.0

echo --- выходной файл ---
call :run -p requests -r %URL% -v 2.31.0 -o graph.png
call :run -p requests -r %URL% -v 2.31.0 -o "a*b.svg"
call :run -p requests -r %URL% -v 2.31.0 -o no_such_dir\graph.svg
call :run -p requests -r %URL% -v 2.31.0 -o src

echo --- глубина анализа ---
call :run -p requests -r %URL% -v 2.31.0 -d abc
call :run -p requests -r %URL% -v 2.31.0 -d 0
call :run -p requests -r %URL% -v 2.31.0 -d 101

echo --- репозиторий пакетов ---
call :run -p requests -r %URL% -v 99.0
call :run -p no-such-package-depviz -r %URL% -v latest
call :run -p requests -r https://pypi.org/simple -v 2.31.0
call :run -p requests -r https://no-such-host.invalid/pypi -v 2.31.0
call :run -p A -r %REPO% -m test
exit /b 0

:run
echo ^> run.bat %*
call %RUN% %*
echo exit code: %ERRORLEVEL%
echo.
exit /b 0
