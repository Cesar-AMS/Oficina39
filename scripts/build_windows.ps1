param(
    [switch]$WithInstaller
)

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

if (-not $WithInstaller) {
    Write-Host "==> Build finalizado (sem instalador)."
    exit 0
}

Write-Host "==> Gerando instalador (Inno Setup)..."
$isccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
)

$iscc = $null
foreach ($candidate in $isccCandidates) {
    if (Test-Path $candidate) {
        $iscc = $candidate
        break
    }
}

if (-not $iscc) {
    throw "ISCC.exe nao encontrado. Instale Inno Setup 6 para gerar o instalador."
}

& $iscc "$root\installer\Oficina39.iss"
Write-Host "==> Instalador pronto em: $artifactsRoot\installer"
