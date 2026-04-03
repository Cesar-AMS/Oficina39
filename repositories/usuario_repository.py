from __future__ import annotations

from sqlalchemy import func

from extensions import db
from models import Usuario


def listar(ativo=None, perfil: str | None = None, termo: str | None = None):
    query = Usuario.query
    if ativo is not None:
        query = query.filter(Usuario.ativo.is_(bool(ativo)))
    if perfil:
        query = query.filter(Usuario.perfil == (perfil or '').strip().lower())
    if termo:
        termo_limpo = (termo or '').strip()
        if termo_limpo:
            filtro = f'%{termo_limpo}%'
            query = query.filter(
                db.or_(
                    Usuario.nome.ilike(filtro),
                    Usuario.email.ilike(filtro),
                )
            )
    return query.order_by(func.lower(Usuario.nome).asc(), Usuario.id.asc()).all()


def buscar_por_id(usuario_id: int):
    return Usuario.query.filter(Usuario.id == usuario_id).first()


def buscar_por_email(email: str):
    termo = (email or '').strip().lower()
    if not termo:
        return None
    return Usuario.query.filter(func.lower(Usuario.email) == termo).first()


def criar(usuario: Usuario):
    db.session.add(usuario)
    db.session.flush()
    return usuario


def salvar():
    db.session.commit()


def contar() -> int:
    return Usuario.query.count()
