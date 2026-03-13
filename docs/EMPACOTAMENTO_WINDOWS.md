# Empacotamento Windows (Distribuição)

Este projeto suporta dois modos:

- `DEV` (manutenção): código aberto no VSCode.
- `DIST` (cliente): instalador `.exe` com atalho na área de trabalho.

## 1) Pré-requisitos (máquina de build)

- Windows 10/11
- Python com ambiente virtual já criado no projeto (`.venv`)
- Inno Setup 6 (opcional, só para gerar instalador)

## 2) Gerar executável (sem instalador)

No PowerShell, na raiz do projeto:

```powershell
.\scripts\build_windows.ps1
```

Saída:

- `artifacts\release\Oficina39\Oficina39.exe`

## 3) Gerar executável + instalador

```powershell
.\scripts\build_windows.ps1 -WithInstaller
```

Saída:

- `artifacts\release\Oficina39\Oficina39.exe`
- `artifacts\installer\Oficina39_Setup_v1.0.0.exe`

## 4) Onde ficam os dados do cliente instalado

No executável empacotado, o sistema usa:

- `%LOCALAPPDATA%\Oficina39\database.db`
- `%LOCALAPPDATA%\Oficina39\uploads\`
- `%LOCALAPPDATA%\Oficina39\backups\`

Isso evita perda de dados ao atualizar versão.

## 5) Fluxo recomendado para venda

1. Manter código-fonte no pendrive (`DEV`).
2. Gerar instalador (`DIST`) com script acima.
3. Entregar apenas o instalador ao cliente.
4. Para atualização, instalar nova versão por cima.

## 6) Ajustar versão do instalador

Edite em `installer/Oficina39.iss`:

- `#define MyAppVersion "1.0.0"`

## 7) Observações

- O app abre em janela própria (`desktop_app.py`), sem depender do navegador.
- Para forçar pasta de dados customizada (suporte técnico), use variável:
  - `OFICINA39_DATA_DIR`
