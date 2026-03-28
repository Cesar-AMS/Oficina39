# Empacotamento Windows

Este projeto usa um unico formato de distribuicao: a pasta do executavel gerada pelo PyInstaller.

## 1) Pre-requisitos

- Windows 10/11
- Python com ambiente virtual ja criado no projeto (`.venv`)

## 2) Gerar executavel

No PowerShell, na raiz do projeto:

```powershell
.\scripts\build_windows.ps1
```

Saida:

- `artifacts\release\Oficina39\Oficina39.exe`

## 3) Como executar

- Execute `artifacts\release\Oficina39\Oficina39.exe`
- Mantenha o `.exe` junto da pasta `_internal`
- Ou use `INICIAR_OFICINA.bat` na raiz do projeto

## 4) Observacoes

- O app abre em janela propria (`desktop_app.py`)
- A entrega correta e a pasta `artifacts\release\Oficina39`
- Nao ha mais suporte a instalador neste projeto
