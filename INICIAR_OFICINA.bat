@echo off
setlocal
title Oficina 39 - Sistema Portátil
color 0A

echo =========================================
echo OFICINA 39 - SISTEMA DE GESTÃO
echo =========================================
echo.

:: Vai para a pasta onde o .bat está (funciona em qualquer pendrive/PC)
cd /d "%~dp0"

echo 📁 Pasta do sistema: %cd%
echo.

:: Se existir versão empacotada, abre direto o executável (modo portátil)
if exist "artifacts\release\Oficina39\Oficina39.exe" (
    echo ✅ Executável encontrado. Abrindo Oficina 39...
    start "" "artifacts\release\Oficina39\Oficina39.exe"
    exit /b 0
)

:: Define o Python a ser usado (prioriza ambiente virtual local)
set "PYTHON_CMD=python"
set "PIP_CMD=pip"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    set "PIP_CMD=.venv\Scripts\pip.exe"
)

:: Verifica se Python está instalado
"%PYTHON_CMD%" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python NAO encontrado!
    echo.
    echo Para usar este sistema, instale o Python:
    echo https://www.python.org/downloads/
    echo.
    echo ⚠️ Marque a opção "Add Python to PATH" durante a instalação
    echo.
    pause
    exit /b 1
)

:: Mostra versão do Python encontrada
for /f "tokens=*" %%i in ('"%PYTHON_CMD%" --version 2^>^&1') do set PY_VERSION=%%i
echo ✅ %PY_VERSION% encontrado!
echo.

:: Verifica se pip está funcionando
"%PIP_CMD%" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Pip nao encontrado, tentando garantir...
    "%PYTHON_CMD%" -m ensurepip --upgrade >nul 2>&1
)

:: Verifica se já tem as dependências (opcional)
if exist requirements.txt (
    echo 📦 Verificando dependencias...
    "%PYTHON_CMD%" -m pip install --no-cache-dir -r requirements.txt --quiet
    if %errorlevel% equ 0 (
        echo ✅ Dependencias verificadas/instaladas
    ) else (
        echo ⚠️ Atencao com as dependencias
    )
) else (
    echo ⚠️ Arquivo requirements.txt nao encontrado
)

echo.
echo 🚀 Iniciando servidor web...
echo.

:: Inicia o servidor Flask em segundo plano
start /B "" "%PYTHON_CMD%" app.py

:: Aguarda 3 segundos para o servidor iniciar
timeout /t 3 /nobreak >nul

:: Abre o navegador
start http://localhost:5000

echo =========================================
echo ✅ SISTEMA INICIADO COM SUCESSO!
echo =========================================
echo.
echo 🌐 Navegador aberto em: http://localhost:5000
echo 📁 Banco de dados: database.db
echo 💻 Feche esta janela para encerrar o sistema
echo.
echo Pressione qualquer tecla para sair...
pause >nul

endlocal
exit
