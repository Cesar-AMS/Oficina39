@echo off
setlocal
title Oficina 39 - Atualizar Banco

cd /d "%~dp0"

set "QUIET=0"
if /I "%~1"=="--quiet" set "QUIET=1"

set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    if "%QUIET%"=="0" (
        echo Ambiente virtual nao encontrado em .venv\Scripts\python.exe
        pause
    )
    exit /b 1
)

if "%QUIET%"=="0" echo Aplicando inicializacao e migracoes leves do banco...
"%PYTHON%" -c "from app import create_app; create_app(start_scheduler=False); print('Banco atualizado com sucesso.')"
if errorlevel 1 (
    if "%QUIET%"=="0" (
        echo Falha ao atualizar o banco de dados.
        pause
    )
    exit /b 1
)

if "%QUIET%"=="0" echo Banco pronto.
exit /b 0
