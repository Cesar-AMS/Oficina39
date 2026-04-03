from __future__ import annotations

from datetime import date, datetime
from math import ceil

from extensions import db
from models import (
    CATEGORIAS_MOVIMENTO_CAIXA,
    FORMAS_MOVIMENTO_CAIXA,
    MovimentoCaixa,
    TIPOS_MOVIMENTO_CAIXA,
)
from repositories.caixa_repository import caixa_repository


def _texto(valor) -> str:
    return (valor or '').strip()


def _float_positivo(valor, campo: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f'{campo} invalido.')
    if numero <= 0:
        raise ValueError(f'{campo} deve ser maior que zero.')
    return numero


def _normalizar_filtros(filtros: dict) -> dict:
    filtros = dict(filtros or {})
    normalizados = {}
    for chave in ('tipo', 'categoria', 'forma_pagamento', 'descricao'):
        if filtros.get(chave):
            normalizados[chave] = _texto(filtros.get(chave))
    for chave in ('ordem_id', 'cliente_id'):
        if filtros.get(chave) not in (None, ''):
            normalizados[chave] = int(filtros.get(chave))
    if filtros.get('data_inicio'):
        normalizados['data_inicio'] = filtros['data_inicio']
    if filtros.get('data_fim'):
        normalizados['data_fim'] = filtros['data_fim']
    return normalizados


def _normalizar_forma_pagamento_legado(forma_pagamento: str | None) -> str | None:
    forma = _texto(forma_pagamento).lower()
    if not forma:
        return None
    mapping = {
        'dinheiro': 'dinheiro',
        'pix': 'pix',
        'cartão': 'cartao',
        'cartao': 'cartao',
        'cartão débito': 'cartao',
        'cartao debito': 'cartao',
        'cartão crédito': 'cartao',
        'cartao credito': 'cartao',
        'transferência': 'debito_conta',
        'transferencia': 'debito_conta',
        'boleto': 'debito_conta',
        'não informado': None,
        'nao informado': None,
    }
    return mapping.get(forma, forma if forma in FORMAS_MOVIMENTO_CAIXA else None)


def _criar_movimento_sem_commit(dados: dict) -> MovimentoCaixa:
    dados = dict(dados or {})
    tipo = _texto(dados.get('tipo')).lower()
    categoria = _texto(dados.get('categoria')).lower()
    forma_pagamento = _normalizar_forma_pagamento_legado(dados.get('forma_pagamento'))

    if tipo not in TIPOS_MOVIMENTO_CAIXA:
        raise ValueError('Tipo de movimento invalido.')
    if categoria not in CATEGORIAS_MOVIMENTO_CAIXA:
        raise ValueError('Categoria de movimento invalida.')
    if forma_pagamento and forma_pagamento not in FORMAS_MOVIMENTO_CAIXA:
        raise ValueError('Forma de pagamento invalida.')

    movimento = MovimentoCaixa(
        tipo=tipo,
        categoria=categoria,
        valor=_float_positivo(dados.get('valor'), 'Valor'),
        data_movimento=dados.get('data_movimento') or datetime.now(),
        ordem_id=dados.get('ordem_id'),
        cliente_id=dados.get('cliente_id'),
        descricao=_texto(dados.get('descricao')) or None,
        forma_pagamento=forma_pagamento,
    )
    caixa_repository.criar(movimento)
    return movimento


def criar_movimento(dados: dict) -> MovimentoCaixa:
    movimento = _criar_movimento_sem_commit(dados)
    db.session.commit()
    return movimento


def registrar_entrada(valor, categoria: str, descricao: str = '', forma_pagamento: str | None = None, ordem_id: int | None = None, cliente_id: int | None = None, data_movimento: datetime | None = None, commit: bool = True) -> MovimentoCaixa:
    movimento = _criar_movimento_sem_commit({
        'tipo': 'entrada',
        'categoria': categoria,
        'valor': valor,
        'descricao': descricao,
        'forma_pagamento': forma_pagamento,
        'ordem_id': ordem_id,
        'cliente_id': cliente_id,
        'data_movimento': data_movimento or datetime.now(),
    })
    if commit:
        db.session.commit()
    return movimento


def registrar_saida(valor, categoria: str, descricao: str = '', forma_pagamento: str | None = None, ordem_id: int | None = None, cliente_id: int | None = None, data_movimento: datetime | None = None, commit: bool = True) -> MovimentoCaixa:
    movimento = _criar_movimento_sem_commit({
        'tipo': 'saida',
        'categoria': categoria,
        'valor': valor,
        'descricao': descricao,
        'forma_pagamento': forma_pagamento,
        'ordem_id': ordem_id,
        'cliente_id': cliente_id,
        'data_movimento': data_movimento or datetime.now(),
    })
    if commit:
        db.session.commit()
    return movimento


def listar_movimentos(filtros: dict, pagina: int = 1, limite: int = 20) -> dict:
    pagina = max(1, int(pagina or 1))
    limite = max(1, min(100, int(limite or 20)))
    itens, total = caixa_repository.listar(_normalizar_filtros(filtros), pagina, limite)
    total_paginas = max(1, ceil(total / limite)) if total else 1
    return {
        'itens': [item.to_dict() for item in itens],
        'pagina': pagina,
        'limite': limite,
        'total': total,
        'total_paginas': total_paginas,
    }


def obter_movimento(id: int) -> MovimentoCaixa:
    movimento = caixa_repository.obter_por_id(id)
    if not movimento:
        raise LookupError('Movimento de caixa nao encontrado.')
    return movimento


def obter_saldo(data_corte: datetime = None) -> float:
    return caixa_repository.obter_saldo(data_corte)


def obter_extrato(data_inicio: datetime, data_fim: datetime, tipo: str = None):
    if data_inicio > data_fim:
        raise ValueError('Data inicial nao pode ser maior que a data final.')
    tipo_normalizado = _texto(tipo).lower() or None
    if tipo_normalizado and tipo_normalizado not in TIPOS_MOVIMENTO_CAIXA:
        raise ValueError('Tipo de movimento invalido.')
    return caixa_repository.obter_extrato(data_inicio, data_fim, tipo_normalizado)


def obter_resumo_diario(data_ref: date) -> dict:
    return caixa_repository.obter_resumo_diario(data_ref)


def obter_movimentos_por_ordem(ordem_id: int):
    return caixa_repository.obter_movimentos_por_ordem(ordem_id)


def obter_movimentos_por_cliente(cliente_id: int):
    return caixa_repository.obter_movimentos_por_cliente(cliente_id)
