from __future__ import annotations

from extensions import db
from models import Comunicacao


def criar(comunicacao: Comunicacao):
    db.session.add(comunicacao)
    db.session.flush()
    return comunicacao


def salvar():
    db.session.commit()


def obter_por_id(comunicacao_id: int):
    return Comunicacao.query.filter(Comunicacao.id == comunicacao_id).first()


def listar(canal=None, status=None, entidade_tipo=None, entidade_id=None, pagina: int = 1, limite: int = 20):
    query = Comunicacao.query
    if canal:
        query = query.filter(Comunicacao.canal == (canal or '').strip().lower())
    if status:
        query = query.filter(Comunicacao.status == (status or '').strip().lower())
    if entidade_tipo:
        query = query.filter(Comunicacao.entidade_tipo == (entidade_tipo or '').strip().lower())
    if entidade_id is not None:
        query = query.filter(Comunicacao.entidade_id == int(entidade_id))

    total = query.count()
    itens = (
        query.order_by(Comunicacao.created_at.desc(), Comunicacao.id.desc())
        .offset(max(0, (pagina - 1) * limite))
        .limit(limite)
        .all()
    )
    return itens, total


def listar_pendentes(limite: int = 50):
    return (
        Comunicacao.query
        .filter(Comunicacao.status == 'pendente')
        .order_by(Comunicacao.created_at.asc(), Comunicacao.id.asc())
        .limit(limite)
        .all()
    )
