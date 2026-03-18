from sqlalchemy import func, or_

from models import Cliente


def listar_todos():
    return Cliente.query.all()


def buscar_por_id(cliente_id):
    return Cliente.query.get(cliente_id)


def buscar_por_cpf(cpf):
    return Cliente.query.filter_by(cpf=cpf).first()


def buscar_por_placa(placa):
    placa = (placa or '').strip().upper()
    if not placa:
        return None
    placa_sem_hifen = placa.replace('-', '')
    placa_coluna = func.replace(func.upper(Cliente.placa), '-', '')
    return Cliente.query.filter(placa_coluna == placa_sem_hifen).first()


def buscar_por_termo(termo, limite=10):
    termo = (termo or '').strip()
    if not termo:
        return []

    termo_numerico = ''.join(ch for ch in termo if ch.isdigit())
    cpf_sem_mascara = func.replace(func.replace(func.replace(Cliente.cpf, '.', ''), '-', ''), '/', '')
    condicoes = [
        Cliente.nome_cliente.ilike(f'%{termo}%'),
        Cliente.cpf.ilike(f'%{termo}%')
    ]
    if termo_numerico:
        condicoes.append(cpf_sem_mascara.ilike(f'%{termo_numerico}%'))

    return Cliente.query.filter(or_(*condicoes)).limit(limite).all()
