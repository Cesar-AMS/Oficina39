from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import func

from extensions import db
from models import MovimentoCaixa


class CaixaRepository:
    def criar(self, movimento: MovimentoCaixa) -> MovimentoCaixa:
        db.session.add(movimento)
        db.session.flush()
        return movimento

    def listar(self, filtros: dict, pagina: int, limite: int):
        filtros = filtros or {}
        query = MovimentoCaixa.query

        if filtros.get('tipo'):
            query = query.filter(MovimentoCaixa.tipo == filtros['tipo'])
        if filtros.get('categoria'):
            query = query.filter(MovimentoCaixa.categoria == filtros['categoria'])
        if filtros.get('ordem_id'):
            query = query.filter(MovimentoCaixa.ordem_id == filtros['ordem_id'])
        if filtros.get('cliente_id'):
            query = query.filter(MovimentoCaixa.cliente_id == filtros['cliente_id'])
        if filtros.get('forma_pagamento'):
            query = query.filter(MovimentoCaixa.forma_pagamento == filtros['forma_pagamento'])
        if filtros.get('descricao'):
            query = query.filter(MovimentoCaixa.descricao.ilike(f"%{filtros['descricao']}%"))
        if filtros.get('data_inicio'):
            query = query.filter(MovimentoCaixa.data_movimento >= filtros['data_inicio'])
        if filtros.get('data_fim'):
            query = query.filter(MovimentoCaixa.data_movimento <= filtros['data_fim'])

        total = query.count()
        itens = (
            query.order_by(MovimentoCaixa.data_movimento.desc(), MovimentoCaixa.id.desc())
            .offset(max(0, (pagina - 1) * limite))
            .limit(limite)
            .all()
        )
        return itens, total

    def obter_por_id(self, id: int) -> MovimentoCaixa | None:
        return db.session.get(MovimentoCaixa, id)

    def obter_saldo(self, data_corte: datetime = None) -> float:
        query = MovimentoCaixa.query
        if data_corte:
            query = query.filter(MovimentoCaixa.data_movimento <= data_corte)

        entradas = (
            query.with_entities(func.coalesce(func.sum(MovimentoCaixa.valor), 0))
            .filter(MovimentoCaixa.tipo == 'entrada')
            .scalar()
        ) or 0
        saidas = (
            query.with_entities(func.coalesce(func.sum(MovimentoCaixa.valor), 0))
            .filter(MovimentoCaixa.tipo == 'saida')
            .scalar()
        ) or 0
        return float(entradas) - float(saidas)

    def obter_extrato(self, data_inicio: datetime, data_fim: datetime, tipo: str = None):
        query = (
            MovimentoCaixa.query
            .filter(MovimentoCaixa.data_movimento >= data_inicio)
            .filter(MovimentoCaixa.data_movimento <= data_fim)
        )
        if tipo:
            query = query.filter(MovimentoCaixa.tipo == tipo)
        return query.order_by(MovimentoCaixa.data_movimento.desc(), MovimentoCaixa.id.desc()).all()

    def obter_resumo_diario(self, data: date) -> dict:
        inicio = datetime.combine(data, time.min)
        fim = datetime.combine(data, time.max)

        entradas = (
            db.session.query(func.coalesce(func.sum(MovimentoCaixa.valor), 0))
            .filter(MovimentoCaixa.tipo == 'entrada')
            .filter(MovimentoCaixa.data_movimento >= inicio, MovimentoCaixa.data_movimento <= fim)
            .scalar()
        ) or 0
        saidas = (
            db.session.query(func.coalesce(func.sum(MovimentoCaixa.valor), 0))
            .filter(MovimentoCaixa.tipo == 'saida')
            .filter(MovimentoCaixa.data_movimento >= inicio, MovimentoCaixa.data_movimento <= fim)
            .scalar()
        ) or 0
        quantidade_entradas = (
            db.session.query(func.count(MovimentoCaixa.id))
            .filter(MovimentoCaixa.tipo == 'entrada')
            .filter(MovimentoCaixa.data_movimento >= inicio, MovimentoCaixa.data_movimento <= fim)
            .scalar()
        ) or 0
        quantidade_saidas = (
            db.session.query(func.count(MovimentoCaixa.id))
            .filter(MovimentoCaixa.tipo == 'saida')
            .filter(MovimentoCaixa.data_movimento >= inicio, MovimentoCaixa.data_movimento <= fim)
            .scalar()
        ) or 0

        return {
            'data': data.isoformat(),
            'total_entradas': float(entradas),
            'total_saidas': float(saidas),
            'saldo': float(entradas) - float(saidas),
            'quantidade_entradas': int(quantidade_entradas),
            'quantidade_saidas': int(quantidade_saidas),
        }

    def obter_movimentos_por_ordem(self, ordem_id: int):
        return (
            MovimentoCaixa.query
            .filter(MovimentoCaixa.ordem_id == ordem_id)
            .order_by(MovimentoCaixa.data_movimento.desc(), MovimentoCaixa.id.desc())
            .all()
        )

    def obter_movimentos_por_cliente(self, cliente_id: int):
        return (
            MovimentoCaixa.query
            .filter(MovimentoCaixa.cliente_id == cliente_id)
            .order_by(MovimentoCaixa.data_movimento.desc(), MovimentoCaixa.id.desc())
            .all()
        )


caixa_repository = CaixaRepository()
