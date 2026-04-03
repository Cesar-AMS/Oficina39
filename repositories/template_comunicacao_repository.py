from __future__ import annotations

from sqlalchemy import func

from extensions import db
from models import TemplateComunicacao


def listar(nome: str | None = None, canal: str | None = None, ativo=None):
    query = TemplateComunicacao.query
    if nome:
        query = query.filter(TemplateComunicacao.nome.ilike(f'%{(nome or "").strip()}%'))
    if canal:
        query = query.filter(TemplateComunicacao.canal == (canal or '').strip().lower())
    if ativo is not None:
        query = query.filter(TemplateComunicacao.ativo.is_(bool(ativo)))
    return query.order_by(func.lower(TemplateComunicacao.nome).asc(), TemplateComunicacao.id.asc()).all()


def buscar_por_id(template_id: int):
    return TemplateComunicacao.query.filter(TemplateComunicacao.id == template_id).first()


def buscar_por_nome(nome: str):
    termo = (nome or '').strip().lower()
    if not termo:
        return None
    return TemplateComunicacao.query.filter(func.lower(TemplateComunicacao.nome) == termo).first()


def criar(template: TemplateComunicacao):
    db.session.add(template)
    db.session.flush()
    return template


def salvar():
    db.session.commit()
