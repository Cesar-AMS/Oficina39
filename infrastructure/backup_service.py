import os
import shutil
from datetime import datetime, timedelta


def _basedir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _backup_dir():
    pasta = os.path.join(_basedir(), 'backups')
    os.makedirs(pasta, exist_ok=True)
    return pasta


def _db_path():
    return os.path.join(_basedir(), 'database.db')


def aplicar_retencao_backups(prefixo='database_backup_', extensao='.db', dias_retencao=15):
    pasta = _backup_dir()
    limite = datetime.now() - timedelta(days=max(1, int(dias_retencao)))
    removidos = 0
    for nome in os.listdir(pasta):
        if not nome.startswith(prefixo) or not nome.endswith(extensao):
            continue
        caminho = os.path.join(pasta, nome)
        if datetime.fromtimestamp(os.path.getmtime(caminho)) < limite:
            try:
                os.remove(caminho)
                removidos += 1
            except Exception:
                pass
    return removidos


def criar_backup_database(prefixo='database_backup_', dias_retencao=15):
    origem = _db_path()
    if not os.path.exists(origem):
        raise FileNotFoundError('database.db não encontrado')

    pasta = _backup_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nome = f'{prefixo}{timestamp}.db'
    destino = os.path.join(pasta, nome)
    shutil.copy2(origem, destino)

    removidos = aplicar_retencao_backups(prefixo=prefixo, extensao='.db', dias_retencao=dias_retencao)
    return {
        'arquivo': nome,
        'caminho': destino,
        'tamanho_bytes': os.path.getsize(destino),
        'removidos_por_retencao': removidos
    }


def status_backups(prefixo='database_backup_', extensao='.db'):
    pasta = _backup_dir()
    arquivos = []
    for nome in os.listdir(pasta):
        if nome.startswith(prefixo) and nome.endswith(extensao):
            caminho = os.path.join(pasta, nome)
            arquivos.append({
                'nome': nome,
                'caminho': caminho,
                'mtime': os.path.getmtime(caminho),
                'tamanho_bytes': os.path.getsize(caminho)
            })
    arquivos.sort(key=lambda x: x['mtime'], reverse=True)
    ultimo = arquivos[0] if arquivos else None
    return {
        'quantidade': len(arquivos),
        'ultimo_arquivo': (ultimo['nome'] if ultimo else None),
        'ultimo_em': (datetime.fromtimestamp(ultimo['mtime']).strftime('%Y-%m-%d %H:%M:%S') if ultimo else None),
        'ultimo_tamanho_bytes': (ultimo['tamanho_bytes'] if ultimo else 0)
    }
