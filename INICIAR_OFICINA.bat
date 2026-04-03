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
set "MODO=silencioso"
set "LOG_DIR=logs"
set "LOG_ARQUIVO=%LOG_DIR%\desktop_debug.log"

if /I "%~1"=="debug" set "MODO=debug"
if /I "%~1"=="verificar" set "MODO=verificar"
if /I "%~1"=="console" set "MODO=verificar"
if /I "%~1"=="ajuda" goto :USO
if /I "%~1"=="help" goto :USO
if /I "%~1"=="--help" goto :USO
if /I "%~1"=="-h" goto :USO

if not exist "%APP%" (
    if exist "%LEGACY_APP%" (
        set "APP=%LEGACY_APP%"
    ) else (
        echo Arquivo main.py nao encontrado.
        pause
        exit /b 1
    )
)

if not exist "%PYTHON%" (
    echo Ambiente virtual nao encontrado em .venv\Scripts\python.exe
    echo.
    echo Execute primeiro:
    echo   python -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo ==========================================
echo Oficina 39 - Inicializacao do Desktop
echo ==========================================
echo.

if exist "%SETUP_BAT%" (
    if /I "%MODO%"=="verificar" echo [1/3] Verificando dependencias...
    call "%SETUP_BAT%" --quiet
    if errorlevel 1 (
        echo Falha ao preparar o ambiente.
        pause
        exit /b 1
    )
)

if exist "%MIGRATE_BAT%" (
    if /I "%MODO%"=="verificar" echo [2/3] Atualizando banco de dados...
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
        echo [3/3] Iniciando Oficina 39 em modo de verificacao...
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

if /I "%MODO%"=="debug" (
    echo [3/3] Iniciando Oficina 39 em modo debug...
    if exist "%PYTHON%" (
        "%PYTHON%" "%APP%"
        exit /b %errorlevel%
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

:USO
echo Uso:
echo   INICIAR_OFICINA.bat
echo   INICIAR_OFICINA.bat verificar
echo   INICIAR_OFICINA.bat debug
echo.
echo Modos:
echo   padrao     - abre o desktop nativo em segundo plano
echo   verificar  - executa com log em logs\desktop_debug.log
echo   debug      - executa no console atual
echo.
pause
exit /b 0
