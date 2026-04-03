@echo off
setlocal
title Oficina 39 - Iniciar Sistema
color 0A

cd /d "%~dp0"

set "PYTHONW=.venv\Scripts\pythonw.exe"
set "PYTHON=.venv\Scripts\python.exe"
set "SETUP_BAT=%~dp0setup.bat"
set "MIGRATE_BAT=%~dp0migrate.bat"
set "APP=main.py"
set "LEGACY_APP=desktop_app.py"
set "WEB_APP=app.py"
set "MODO=silencioso"
set "LOG_DIR=logs"
set "LOG_ARQUIVO=%LOG_DIR%\desktop_debug.log"

if /I "%~1"=="debug" set "MODO=debug"
if /I "%~1"=="verificar" set "MODO=verificar"
if /I "%~1"=="console" set "MODO=verificar"

if not exist "%APP%" (
    if exist "%LEGACY_APP%" (
        set "APP=%LEGACY_APP%"
    ) else (
        echo Arquivo main.py nao encontrado.
        pause
        exit /b 1
    )
)

if exist "%SETUP_BAT%" (
    call "%SETUP_BAT%" --quiet
    if errorlevel 1 (
        echo Falha ao preparar o ambiente.
        pause
        exit /b 1
    )
)

if exist "%MIGRATE_BAT%" (
    call "%MIGRATE_BAT%" --quiet
    if errorlevel 1 (
        echo Falha ao atualizar o banco de dados.
        pause
        exit /b 1
    )
)

if /I "%MODO%"=="verificar" (
    if exist "%PYTHON%" (
        if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
        echo Iniciando Oficina 39 em modo de verificacao desktop...
        echo O console ficara aberto para mostrar erros da inicializacao nativa.
        echo O log desta execucao sera salvo em: %LOG_ARQUIVO%
        echo.
        echo ===== %date% %time% | modo=verificar =====>>"%LOG_ARQUIVO%"
        "%PYTHON%" "%APP%" >>"%LOG_ARQUIVO%" 2>&1
        set "EXIT_CODE=%errorlevel%"
        echo.
        echo O sistema foi encerrado com codigo: %EXIT_CODE%
        echo Se algo falhar, confira o arquivo: %LOG_ARQUIVO%
        echo Pressione qualquer tecla para fechar.
        pause >nul
        exit /b %EXIT_CODE%
    )
)

if exist "%PYTHONW%" (
    start "" "%PYTHONW%" "%APP%"
    exit /b 0
)

if exist "%PYTHON%" (
    start "" "%PYTHON%" "%APP%"
    exit /b 0
)

echo Ambiente virtual nao encontrado em .venv\Scripts.
echo.
pause
exit /b 1
