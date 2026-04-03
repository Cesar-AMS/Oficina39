from __future__ import annotations

from datetime import datetime

from sqlalchemy import func

from extensions import db
from models import ApiKey


def listar(ativa=None, termo: str | None = None):
    query = ApiKey.query
    if ativa is not None:
        query = query.filter(ApiKey.ativa.is_(bool(ativa)))
    if termo:
        filtro = f"%{(termo or '').strip()}%"
        query = query.filter(
            db.or_(
                ApiKey.nome.ilike(filtro),
                ApiKey.key.ilike(filtro),
            )
        )
    return query.order_by(func.lower(ApiKey.nome).asc(), ApiKey.id.asc()).all()


def buscar_por_id(api_key_id: int):
    return ApiKey.query.filter(ApiKey.id == api_key_id).first()


def buscar_por_key(chave: str):
    termo = (chave or '').strip()
    if not termo:
        return None
    return ApiKey.query.filter(ApiKey.key == termo).first()


def criar(api_key: ApiKey):
    db.session.add(api_key)
    db.session.flush()
    return api_key


def salvar():
    db.session.commit()


def marcar_uso(api_key: ApiKey, quando: datetime | None = None):
    api_key.ultimo_uso = quando or datetime.now()
    db.session.commit()
