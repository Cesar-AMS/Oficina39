from models import Profissional
from extensions import db


def listar(ativos_apenas=True):
    query = Profissional.query
    if ativos_apenas:
        query = query.filter(Profissional.ativo.is_(True))
    return query.order_by(Profissional.nome.asc()).all()


def buscar_por_id(profissional_id):
    return db.session.get(Profissional, profissional_id)


def buscar_por_nome(nome):
    return Profissional.query.filter(Profissional.nome == nome).first()


def buscar_por_cnpj(cnpj):
    return Profissional.query.filter(Profissional.cnpj == cnpj).first()


def buscar_outro_por_nome(nome, profissional_id):
    return Profissional.query.filter(Profissional.nome == nome, Profissional.id != profissional_id).first()


def buscar_outro_por_cnpj(cnpj, profissional_id):
    return Profissional.query.filter(Profissional.cnpj == cnpj, Profissional.id != profissional_id).first()
