$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $root
Set-Location $root
$artifactsRoot = Join-Path $root "artifacts"
$buildWorkRoot = Join-Path $artifactsRoot "build-work"
$releaseRoot = Join-Path $artifactsRoot "release"

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Python do ambiente virtual nao encontrado em .venv\Scripts\python.exe."
}

Write-Host "==> Instalando/atualizando dependencias de build..."
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt
& $python -m pip install pyinstaller

Write-Host "==> Limpando builds anteriores..."
New-Item -ItemType Directory -Force -Path $artifactsRoot | Out-Null
Remove-Item -Recurse -Force $buildWorkRoot -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $releaseRoot -ErrorAction SilentlyContinue

Write-Host "==> Gerando executavel (PyInstaller)..."
& $python -m PyInstaller --noconfirm --workpath $buildWorkRoot --distpath $releaseRoot "$root\Oficina39.spec"

Write-Host "==> Executavel pronto em: $releaseRoot\Oficina39\Oficina39.exe"
Write-Host "==> Build finalizado."
