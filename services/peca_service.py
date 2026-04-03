from __future__ import annotations

from math import ceil

from extensions import db
from models import Peca
from repositories import peca_repository


def _normalizar_texto(valor):
    return (valor or '').strip()


def _normalizar_float(valor, campo: str, padrao: float = 0.0) -> float:
    try:
        return float(valor if valor not in (None, '') else padrao)
    except (TypeError, ValueError):
        raise ValueError(f'{campo} invalido.')


def _normalizar_payload(dados: dict) -> dict:
    payload = dict(dados or {})
    payload['codigo'] = _normalizar_texto(payload.get('codigo'))
    payload['nome'] = _normalizar_texto(payload.get('nome'))
    payload['categoria'] = _normalizar_texto(payload.get('categoria'))
    payload['descricao'] = _normalizar_texto(payload.get('descricao'))
    payload['estoque_atual'] = _normalizar_float(payload.get('estoque_atual'), 'Estoque', 0.0)
    payload['valor_custo'] = _normalizar_float(payload.get('valor_custo'), 'Valor de custo', 0.0)
    payload['percentual_lucro'] = _normalizar_float(payload.get('percentual_lucro'), 'Percentual de lucro', 0.0)
    payload['valor_unitario'] = _normalizar_float(payload.get('valor_unitario'), 'Valor unitario', 0.0)
    if 'ativo' in payload:
        payload['ativo'] = bool(payload.get('ativo'))
    return payload


def listar_pecas(filtros: dict, pagina: int = 1, limite: int = 20) -> dict:
    pagina = max(1, int(pagina or 1))
    limite = max(1, min(100, int(limite or 20)))
    filtros = filtros or {}

    itens, total = peca_repository.listar(
        nome=filtros.get('nome'),
        categoria=filtros.get('categoria'),
        pagina=pagina,
        limite=limite,
    )
    total_paginas = max(1, ceil(total / limite)) if total else 1
    return {
        'itens': [item.to_dict() for item in itens],
        'pagina': pagina,
        'limite': limite,
        'total': total,
        'total_paginas': total_paginas,
    }


def obter_peca(id: int) -> Peca:
    peca = peca_repository.buscar_por_id(id)
    if not peca:
        raise LookupError('Peca nao encontrada.')
    return peca


def criar_peca(dados: dict) -> Peca:
    payload = _normalizar_payload(dados)
    if not payload['nome']:
        raise ValueError('Nome da peca e obrigatorio.')
    if not payload['codigo']:
        raise ValueError('Codigo da peca e obrigatorio.')

    if peca_repository.buscar_por_nome_exato(payload['nome'], incluir_excluidas=True):
        raise ValueError('Ja existe peca com este nome.')
    if peca_repository.buscar_por_codigo_exato(payload['codigo'], incluir_excluidas=True):
        raise ValueError('Ja existe peca com este codigo.')

    peca = Peca(
        codigo=payload['codigo'],
        nome=payload['nome'],
        categoria=payload['categoria'] or None,
        descricao=payload['descricao'] or None,
        estoque_atual=payload['estoque_atual'],
        valor_custo=payload['valor_custo'],
        percentual_lucro=payload['percentual_lucro'],
        valor_unitario=payload['valor_unitario'],
        ativo=payload.get('ativo', True),
    )
    peca_repository.criar(peca)
    peca_repository.salvar()
    return peca


def atualizar_peca(id: int, dados: dict) -> Peca:
    peca = obter_peca(id)
    payload = _normalizar_payload(dados)

    if 'nome' in dados:
        if not payload['nome']:
            raise ValueError('Nome da peca e obrigatorio.')
        existente = peca_repository.buscar_por_nome_exato(payload['nome'], incluir_excluidas=True)
        if existente and existente.id != peca.id:
            raise ValueError('Ja existe peca com este nome.')
        peca.nome = payload['nome']

    if 'codigo' in dados:
        if not payload['codigo']:
            raise ValueError('Codigo da peca e obrigatorio.')
        existente = peca_repository.buscar_por_codigo_exato(payload['codigo'], incluir_excluidas=True)
        if existente and existente.id != peca.id:
            raise ValueError('Ja existe peca com este codigo.')
        peca.codigo = payload['codigo']

    if 'categoria' in dados:
        peca.categoria = payload['categoria'] or None
    if 'descricao' in dados:
        peca.descricao = payload['descricao'] or None
    if 'estoque_atual' in dados:
        if payload['estoque_atual'] < 0:
            raise ValueError('Estoque nao pode ser negativo.')
        peca.estoque_atual = payload['estoque_atual']
    if 'valor_custo' in dados:
        peca.valor_custo = payload['valor_custo']
    if 'percentual_lucro' in dados:
        peca.percentual_lucro = payload['percentual_lucro']
    if 'valor_unitario' in dados:
        peca.valor_unitario = payload['valor_unitario']
    if 'ativo' in dados:
        peca.ativo = payload['ativo']

    peca_repository.salvar()
    return peca


def excluir_peca(id: int) -> bool:
    peca = obter_peca(id)
    if peca_repository.verificar_vinculo_os_ativas(peca.id):
        raise ValueError('Peca vinculada a ordem ativa nao pode ser excluida.')

    peca_repository.soft_delete(peca)
    peca_repository.salvar()
    return True


def baixar_estoque(peca_id: int, quantidade: float) -> Peca:
    peca = obter_peca(peca_id)
    quantidade = _normalizar_float(quantidade, 'Quantidade')
    if quantidade <= 0:
        raise ValueError('Quantidade deve ser maior que zero.')
    if float(peca.estoque_atual or 0) - quantidade < 0:
        raise ValueError('Estoque insuficiente para a baixa informada.')

    peca.estoque_atual = float(peca.estoque_atual or 0) - quantidade
    peca_repository.salvar()
    return peca


def repor_estoque(peca_id: int, quantidade: float) -> Peca:
    peca = obter_peca(peca_id)
    quantidade = _normalizar_float(quantidade, 'Quantidade')
    if quantidade <= 0:
        raise ValueError('Quantidade deve ser maior que zero.')

    peca.estoque_atual = float(peca.estoque_atual or 0) + quantidade
    peca_repository.salvar()
    return peca


def adicionar_peca_em_ordem(ordem, peca_id: int, quantidade: float = 1, valor_unitario=None):
    from models import ItemPeca

    peca = obter_peca(peca_id)
    quantidade_normalizada = _normalizar_float(quantidade, 'Quantidade', 1.0)
    if quantidade_normalizada <= 0:
        raise ValueError('Quantidade deve ser maior que zero.')

    valor_venda = (
        _normalizar_float(valor_unitario, 'Valor unitario', float(peca.valor_unitario or 0))
        if valor_unitario is not None
        else float(peca.valor_unitario or 0)
    )

    item = ItemPeca(
        ordem_id=ordem.id,
        codigo_peca=peca.codigo,
        descricao_peca=peca.nome,
        quantidade=quantidade_normalizada,
        valor_custo=float(peca.valor_custo or 0),
        percentual_lucro=float(peca.percentual_lucro or 0),
        valor_unitario=valor_venda,
    )
    db.session.add(item)
    db.session.flush()
    return item


def calcular_valor_venda_peca(dados_peca):
    valor_unitario = float(dados_peca.get('valor_unitario') or 0)
    valor_custo = float(dados_peca.get('valor_custo') or 0)
    percentual_lucro = float(dados_peca.get('percentual_lucro') or 0)

    if valor_unitario > 0:
        return valor_unitario, valor_custo, percentual_lucro

    valor_unitario = valor_custo * (1 + (percentual_lucro / 100))
    return valor_unitario, valor_custo, percentual_lucro


def calcular_total_pecas(pecas) -> float:
    return sum(float((item.quantidade or 0) * (item.valor_unitario or 0)) for item in pecas)


def anexar_pecas_em_ordem(ordem, pecas_payload: list[dict]):
    from models import ItemPeca

    itens = []
    for peca in pecas_payload or []:
        if not peca.get('descricao_peca'):
            continue
        valor_unitario, valor_custo, percentual_lucro = calcular_valor_venda_peca(peca)
        item = ItemPeca(
            ordem_id=ordem.id,
            codigo_peca=peca.get('codigo_peca', ''),
            descricao_peca=peca['descricao_peca'],
            quantidade=peca.get('quantidade', 1),
            valor_custo=valor_custo,
            percentual_lucro=percentual_lucro,
            valor_unitario=valor_unitario,
        )
        db.session.add(item)
        itens.append(item)
    db.session.flush()
    return itens


def substituir_pecas_da_ordem(ordem, pecas_payload: list[dict]):
    from models import ItemPeca

    ItemPeca.query.filter_by(ordem_id=ordem.id).delete()
    return anexar_pecas_em_ordem(ordem, pecas_payload)


def duplicar_pecas_da_ordem(origem, nova_ordem):
    from models import ItemPeca

    itens = []
    for peca in origem.pecas:
        item = ItemPeca(
            ordem_id=nova_ordem.id,
            codigo_peca=peca.codigo_peca,
            descricao_peca=peca.descricao_peca,
            quantidade=peca.quantidade or 0,
            valor_custo=peca.valor_custo or 0,
            percentual_lucro=peca.percentual_lucro or 0,
            valor_unitario=peca.valor_unitario or 0,
        )
        db.session.add(item)
        itens.append(item)
    db.session.flush()
    return itens


def listar_pecas_com_filtro_periodo(data_inicio, data_fim):
    from sqlalchemy import func
    from models import ItemPeca, Ordem

    data_ref_expr = func.coalesce(
        Ordem.data_conclusao,
        Ordem.data_emissao,
        Ordem.data_entrada,
    )

    rows = (
        ItemPeca.query
        .join(Ordem, ItemPeca.ordem_id == Ordem.id)
        .with_entities(
            Ordem.id.label('ordem_id'),
            data_ref_expr.label('data_ref'),
            ItemPeca.descricao_peca.label('descricao'),
            func.coalesce(ItemPeca.quantidade, 0.0).label('quantidade'),
            func.coalesce(ItemPeca.valor_unitario, 0.0).label('valor_unitario'),
        )
        .filter(data_ref_expr >= data_inicio)
        .filter(data_ref_expr <= data_fim)
        .order_by(data_ref_expr.desc())
        .all()
    )

    return [{
        'ordem_id': row.ordem_id,
        'data_referencia': row.data_ref.strftime('%d/%m/%Y') if row.data_ref else '---',
        'data_ordem': row.data_ref.isoformat() if row.data_ref else '',
        'descricao': row.descricao or '---',
        'quantidade': float(row.quantidade or 0),
        'valor_unitario': float(row.valor_unitario or 0),
        'valor_total': float((row.quantidade or 0) * (row.valor_unitario or 0)),
    } for row in rows]
