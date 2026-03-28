@echo off
setlocal
title Oficina 39 - Iniciar Sistema
color 0A

cd /d "%~dp0"

set "EXE_SAFE=artifacts\release-safe\Oficina39\Oficina39.exe"
set "EXE_PADRAO=artifacts\release\Oficina39\Oficina39.exe"
set "EXE_BUILD_SAFE=artifacts\build-work-safe\Oficina39\Oficina39.exe"
set "EXE_BUILD=artifacts\build-work\Oficina39\Oficina39.exe"

echo =========================================
echo OFICINA 39 - SISTEMA DE GESTAO
echo =========================================
echo.
echo Pasta do sistema: %cd%
echo.

if exist "%EXE_SAFE%" (
    echo Abrindo versao atualizada...
    start "" "%EXE_SAFE%"
    exit /b 0
)

if exist "%EXE_PADRAO%" (
    echo Abrindo versao padrao...
    start "" "%EXE_PADRAO%"
    exit /b 0
)

if exist "%EXE_BUILD_SAFE%" (
    echo Abrindo versao de trabalho segura...
    start "" "%EXE_BUILD_SAFE%"
    exit /b 0
)

if exist "%EXE_BUILD%" (
    echo Abrindo versao de trabalho...
    start "" "%EXE_BUILD%"
    exit /b 0
)

echo Nenhum executavel foi encontrado.
echo.
echo Caminhos verificados:
echo - %EXE_SAFE%
echo - %EXE_PADRAO%
echo - %EXE_BUILD_SAFE%
echo - %EXE_BUILD%
echo.
echo Gere o executavel com:
echo .\scripts\build_windows.ps1
echo.
pause
exit /b 1
