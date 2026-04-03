@echo off
setlocal
title Oficina 39 - Preparar Ambiente

cd /d "%~dp0"

set "QUIET=0"
if /I "%~1"=="--quiet" set "QUIET=1"

set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    if "%QUIET%"=="0" (
        echo Ambiente virtual nao encontrado em .venv\Scripts\python.exe
        echo Crie a .venv antes de executar este script.
        pause
    )
    exit /b 1
)

if "%QUIET%"=="0" echo Verificando dependencias da Oficina 39...
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    if "%QUIET%"=="0" (
        echo Falha ao instalar ou atualizar dependencias.
        pause
    )
    exit /b 1
)

if "%QUIET%"=="0" echo Ambiente pronto.
exit /b 0
