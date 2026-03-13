# Instalacao via Pendrive (Windows)

## Objetivo
Instalar o sistema localmente no computador do cliente e criar atalho na Area de Trabalho para abrir com duplo clique.

## Como usar
1. Copie a pasta do projeto para o pendrive.
2. No computador do cliente, abra a pasta do pendrive.
3. Execute `INSTALAR_OFICINA_WINDOWS.bat` como usuario normal.
4. Aguarde o fim da instalacao.
5. Use o atalho `Oficina 39` criado na Area de Trabalho.

## O que o instalador faz
- Copia a aplicacao para:
  - `%LOCALAPPDATA%\Oficina39`
- Cria ambiente virtual Python em:
  - `%LOCALAPPDATA%\Oficina39\.venv`
- Instala dependencias do `requirements.txt`
- Inicializa a aplicacao e banco local
- Cria atalho `.lnk` na Area de Trabalho

## Execucao do sistema
- Duplo clique no atalho `Oficina 39`
- O sistema abre em janela propria (app desktop, sem navegador)

## Reinstalacao/Atualizacao
- Execute novamente `INSTALAR_OFICINA_WINDOWS.bat`
- O banco local existente (`database.db`) no destino e preservado.

## Requisitos
- Windows 10/11
- Python 3 instalado (`py` ou `python` no PATH)
- WebView2 Runtime (normalmente ja presente no Windows 10/11)
