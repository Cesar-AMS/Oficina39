# Oficina 39 System

Sistema de gestão para oficina mecânica, desenvolvido com foco em operação local no Windows, controle de ordens de serviço, fluxo de caixa, relatórios e emissão de PDF.

## Visão geral

O projeto foi pensado para uso prático no dia a dia da oficina:

- cadastro de clientes e veículos
- abertura, edição e consulta de ordens de serviço
- controle de profissionais cadastrados
- fluxo de caixa com entradas e saídas
- relatórios operacionais e por profissional
- exportação e importação de dados
- geração de recibo/ordem em PDF
- execução no navegador ou em janela própria via executável

## Stack

- Python 3.13
- Flask
- SQLAlchemy
- SQLite
- HTML, CSS e JavaScript
- ReportLab
- PyInstaller
- pywebview

## Estrutura do projeto

```text
app.py                  # Inicialização da aplicação Flask
desktop_app.py          # Execução em janela própria
extensions.py           # Extensões e scheduler
models/                 # Modelos de dados
routes/                 # Rotas HTML e APIs
services/               # Regras de negócio e serviços auxiliares
templates/              # Páginas HTML
static/                 # CSS, JS e imagens
tests/                  # Testes automatizados
scripts/                # Scripts de build
installer/              # Arquivos do instalador Windows
docs/                   # Documentação complementar
artifacts/              # Saída de builds e instaladores
```

## Requisitos

- Windows 10 ou 11
- Python 3.13 instalado
- Ambiente virtual em `.venv`

## Como rodar em desenvolvimento

No PowerShell, dentro da raiz do projeto:

```powershell
.venv\Scripts\python.exe app.py
```

Depois abra:

```text
http://localhost:5000
```

## Como iniciar pelo atalho local

Também é possível iniciar com:

```text
INICIAR_OFICINA.bat
```

Esse arquivo prioriza o executável empacotado quando ele existe em `artifacts/release/Oficina39`.

## Como gerar o executável

```powershell
.\scripts\build_windows.ps1
```

Saída esperada:

```text
artifacts\release\Oficina39\Oficina39.exe
```

Para gerar executável + instalador:

```powershell
.\scripts\build_windows.ps1 -WithInstaller
```

Saída adicional:

```text
artifacts\installer\
```

## Testes

Para rodar os testes automatizados:

```powershell
.venv\Scripts\python.exe -m unittest tests/test_smoke_api.py
```

## O que não sobe para o GitHub

O repositório foi preparado para não versionar arquivos locais ou gerados:

- banco `database.db`
- ambiente virtual `.venv`
- pasta `artifacts`
- uploads
- backups
- arquivos temporários

## Documentação adicional

Arquivos úteis na pasta [docs](./docs):

- `EMPACOTAMENTO_WINDOWS.md`
- `INSTALACAO_PENDRIVE_WINDOWS.md`
- `OPERACAO_DIARIA_BACKUP_RESTORE.md`
- `HOMOLOGACAO_RELEASE.md`

## Autor

Desenvolvido por Cesar Augusto  
Formação: Análise e Desenvolvimento de Sistemas
