from __future__ import annotations

from datetime import datetime

from sqlalchemy import func

from extensions import db
from models import ItemPeca, Ordem, Peca


STATUS_ORDENS_ATIVAS = {'Aguardando', 'Aguardando pecas', 'Em andamento'}


def _query_base(incluir_excluidas: bool = False):
    query = Peca.query
    if not incluir_excluidas:
        query = query.filter(Peca.deleted_at.is_(None)).filter(Peca.ativo.is_(True))
    return query


def listar(nome: str | None = None, categoria: str | None = None, pagina: int = 1, limite: int = 20):
    query = _query_base()

    if nome:
        termo = (nome or '').strip()
        query = query.filter(
            db.or_(
                Peca.nome.ilike(f'%{termo}%'),
                Peca.codigo.ilike(f'%{termo}%')
            )
        )

    if categoria:
        termo_categoria = (categoria or '').strip()
        query = query.filter(Peca.categoria.ilike(f'%{termo_categoria}%'))

    total = query.count()
    itens = (
        query.order_by(func.lower(Peca.nome).asc(), Peca.id.asc())
        .offset(max(0, (pagina - 1) * limite))
        .limit(limite)
        .all()
    )
    return itens, total


def buscar_por_id(peca_id: int, incluir_excluidas: bool = False):
    query = _query_base(incluir_excluidas=incluir_excluidas)
    return query.filter(Peca.id == peca_id).first()


def buscar_por_nome_exato(nome: str, incluir_excluidas: bool = False):
    termo = (nome or '').strip()
    if not termo:
        return None
    query = _query_base(incluir_excluidas=incluir_excluidas)
    return query.filter(func.lower(Peca.nome) == termo.lower()).first()


def buscar_por_codigo_exato(codigo: str, incluir_excluidas: bool = False):
    termo = (codigo or '').strip()
    if not termo:
        return None
    query = _query_base(incluir_excluidas=incluir_excluidas)
    return query.filter(func.lower(Peca.codigo) == termo.lower()).first()


def criar(peca: Peca):
    db.session.add(peca)
    db.session.flush()
    return peca


def salvar():
    db.session.commit()


def verificar_vinculo_os_ativas(peca_id: int) -> bool:
    peca = buscar_por_id(peca_id, incluir_excluidas=True)
    if not peca:
        return False

    nome = (peca.nome or '').strip()
    codigo = (peca.codigo or '').strip()

    query = (
        db.session.query(ItemPeca.id)
        .join(Ordem, Ordem.id == ItemPeca.ordem_id)
        .filter(Ordem.status.in_(STATUS_ORDENS_ATIVAS))
    )

    filtros = []
    if nome:
        filtros.append(func.lower(ItemPeca.descricao_peca) == nome.lower())
    if codigo:
        filtros.append(func.lower(ItemPeca.codigo_peca) == codigo.lower())

    if not filtros:
        return False

    return query.filter(db.or_(*filtros)).first() is not None


def soft_delete(peca: Peca):
    peca.ativo = False
    peca.deleted_at = datetime.now()
    db.session.flush()
    return peca
