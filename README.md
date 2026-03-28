# Oficina 39 System

Sistema de gestao para oficina mecanica, com operacao local no Windows, ordens de servico, fluxo de caixa, relatorios e emissao de PDF.

## Visao geral

- cadastro de clientes e veiculos
- abertura, edicao e consulta de ordens de servico
- controle de profissionais cadastrados
- fluxo de caixa com entradas e saidas
- relatorios operacionais e por profissional
- exportacao e importacao de dados
- geracao de recibo/ordem em PDF

## Stack

- Python 3.13+
- Flask
- SQLAlchemy
- SQLite
- HTML, CSS e JavaScript
- ReportLab

## Estrutura do projeto

```text
app.py                  # Inicializacao da aplicacao Flask
extensions.py           # Extensoes e scheduler
controllers/            # Controllers Flask (APIs e paginas)
models/                 # Modelos de dados
repositories/           # Consultas e filtros reutilizaveis
services/               # Regras de negocio
integrations/           # Integracoes externas
utils/                  # Formatacao e normalizacao
infrastructure/         # Suporte tecnico (email, backup, PDF, log)
views/                  # Paginas HTML
static/                 # CSS, JS e imagens
tests/                  # Testes automatizados
docs/                   # Documentacao complementar
```

## Requisitos

- Windows 10 ou 11
- Python instalado
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

## Testes

```powershell
.venv\Scripts\python.exe -m unittest tests/test_smoke_api.py
```

## Documentacao adicional

Arquivos uteis na pasta [docs](./docs):

- `OPERACAO_DIARIA_BACKUP_RESTORE.md`
- `HOMOLOGACAO_RELEASE.md`
