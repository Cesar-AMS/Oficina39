from __future__ import annotations

from datetime import datetime

from sqlalchemy import func

from extensions import db
from models import ItemServico, Ordem, Servico


STATUS_ORDENS_ATIVAS = {'Aguardando', 'Aguardando pecas', 'Em andamento'}


def _query_base(incluir_excluidos: bool = False):
    query = Servico.query
    if not incluir_excluidos:
        query = query.filter(Servico.deleted_at.is_(None)).filter(Servico.ativo.is_(True))
    return query


def listar(nome: str | None = None, categoria: str | None = None, pagina: int = 1, limite: int = 20):
    query = _query_base()

    if nome:
        termo = (nome or '').strip()
        query = query.filter(Servico.nome.ilike(f'%{termo}%'))

    if categoria:
        termo_categoria = (categoria or '').strip()
        query = query.filter(Servico.categoria.ilike(f'%{termo_categoria}%'))

    total = query.count()
    itens = (
        query.order_by(func.lower(Servico.nome).asc(), Servico.id.asc())
        .offset(max(0, (pagina - 1) * limite))
        .limit(limite)
        .all()
    )
    return itens, total


def buscar_por_id(servico_id: int, incluir_excluidos: bool = False):
    query = _query_base(incluir_excluidos=incluir_excluidos)
    return query.filter(Servico.id == servico_id).first()


def buscar_por_nome_exato(nome: str, incluir_excluidos: bool = False):
    termo = (nome or '').strip()
    if not termo:
        return None
    query = _query_base(incluir_excluidos=incluir_excluidos)
    return query.filter(func.lower(Servico.nome) == termo.lower()).first()


def buscar_por_nome(nome: str, limite: int | None = None):
    termo = (nome or '').strip()
    query = _query_base()
    if termo:
        query = query.filter(Servico.nome.ilike(f'%{termo}%'))
    query = query.order_by(func.lower(Servico.nome).asc(), Servico.id.asc())
    if limite:
        query = query.limit(limite)
    return query.all()


def criar(servico: Servico):
    db.session.add(servico)
    db.session.flush()
    return servico


def salvar():
    db.session.commit()


def possui_vinculo_em_ordem_ativa(servico: Servico) -> bool:
    nome = (servico.nome or '').strip()
    if not nome:
        return False

    return (
        db.session.query(ItemServico.id)
        .join(Ordem, Ordem.id == ItemServico.ordem_id)
        .filter(func.lower(ItemServico.descricao_servico) == nome.lower())
        .filter(Ordem.status.in_(STATUS_ORDENS_ATIVAS))
        .first()
        is not None
    )


def soft_delete(servico: Servico):
    servico.ativo = False
    servico.deleted_at = datetime.now()
    db.session.flush()
    return servico
