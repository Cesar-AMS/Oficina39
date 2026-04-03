from __future__ import annotations

from extensions import db
from models import Webhook


def listar(ativo=None, evento: str | None = None):
    query = Webhook.query
    if ativo is not None:
        query = query.filter(Webhook.ativo.is_(bool(ativo)))
    itens = query.order_by(Webhook.id.asc()).all()
    if evento:
        evento_limpo = (evento or '').strip().lower()
        itens = [item for item in itens if item.aceita_evento(evento_limpo)]
    return itens


def buscar_por_id(webhook_id: int):
    return Webhook.query.filter(Webhook.id == webhook_id).first()


def criar(webhook: Webhook):
    db.session.add(webhook)
    db.session.flush()
    return webhook


def salvar():
    db.session.commit()
