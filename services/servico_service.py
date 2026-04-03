from __future__ import annotations

from math import ceil

from extensions import db
from models import Servico
from repositories import servico_repository


def _normalizar_texto(valor):
    return (valor or '').strip()


def _normalizar_float(valor, padrao: float = 0.0) -> float:
    try:
        return float(valor if valor not in (None, '') else padrao)
    except (TypeError, ValueError):
        raise ValueError('Valor padrao invalido.')


def _normalizar_payload(dados: dict) -> dict:
    payload = dict(dados or {})
    payload['nome'] = _normalizar_texto(payload.get('nome'))
    payload['categoria'] = _normalizar_texto(payload.get('categoria'))
    payload['descricao'] = _normalizar_texto(payload.get('descricao'))
    payload['valor_padrao'] = _normalizar_float(payload.get('valor_padrao'), 0.0)
    if 'ativo' in payload:
        payload['ativo'] = bool(payload.get('ativo'))
    return payload


def listar_servicos(filtros: dict, pagina: int = 1, limite: int = 20) -> dict:
    pagina = max(1, int(pagina or 1))
    limite = max(1, min(100, int(limite or 20)))
    filtros = filtros or {}

    itens, total = servico_repository.listar(
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


def obter_servico(id: int) -> Servico:
    servico = servico_repository.buscar_por_id(id)
    if not servico:
        raise LookupError('Servico nao encontrado.')
    return servico


def criar_servico(dados: dict) -> Servico:
    payload = _normalizar_payload(dados)
    if not payload['nome']:
        raise ValueError('Nome do servico e obrigatorio.')

    existente = servico_repository.buscar_por_nome_exato(payload['nome'], incluir_excluidos=True)
    if existente:
        raise ValueError('Ja existe servico com este nome.')

    servico = Servico(
        nome=payload['nome'],
        categoria=payload['categoria'] or None,
        descricao=payload['descricao'] or None,
        valor_padrao=payload['valor_padrao'],
        ativo=payload.get('ativo', True),
    )
    servico_repository.criar(servico)
    servico_repository.salvar()
    return servico


def atualizar_servico(id: int, dados: dict) -> Servico:
    servico = obter_servico(id)
    payload = _normalizar_payload(dados)

    if 'nome' in dados:
        if not payload['nome']:
            raise ValueError('Nome do servico e obrigatorio.')
        existente = servico_repository.buscar_por_nome_exato(payload['nome'], incluir_excluidos=True)
        if existente and existente.id != servico.id:
            raise ValueError('Ja existe servico com este nome.')
        servico.nome = payload['nome']

    if 'categoria' in dados:
        servico.categoria = payload['categoria'] or None
    if 'descricao' in dados:
        servico.descricao = payload['descricao'] or None
    if 'valor_padrao' in dados:
        servico.valor_padrao = payload['valor_padrao']
    if 'ativo' in dados:
        servico.ativo = payload['ativo']

    servico_repository.salvar()
    return servico


def excluir_servico(id: int) -> bool:
    servico = obter_servico(id)
    if servico_repository.possui_vinculo_em_ordem_ativa(servico):
        raise ValueError('Servico vinculado a ordem ativa nao pode ser excluido.')

    servico_repository.soft_delete(servico)
    servico_repository.salvar()
    return True


def buscar_por_nome(nome: str):
    return servico_repository.buscar_por_nome(nome)


def adicionar_servico_em_ordem(ordem, servico_id: int, nome_profissional: str | None = None, valor_servico=None):
    from models import ItemServico

    servico = obter_servico(servico_id)
    item = ItemServico(
        ordem_id=ordem.id,
        codigo_servico=str(servico.id),
        descricao_servico=servico.nome,
        nome_profissional=(nome_profissional or ordem.profissional_responsavel or '').strip(),
        valor_servico=_normalizar_float(valor_servico, float(servico.valor_padrao or 0)),
    )
    db.session.add(item)
    db.session.flush()
    return item


def calcular_total_servicos(servicos) -> float:
    return sum(float(item.valor_servico or 0) for item in servicos)


def anexar_servicos_em_ordem(ordem, servicos_payload: list[dict]):
    from models import ItemServico

    itens = []
    for servico in servicos_payload or []:
        if not servico.get('descricao_servico'):
            continue
        item = ItemServico(
            ordem_id=ordem.id,
            codigo_servico=servico.get('codigo_servico', ''),
            descricao_servico=servico['descricao_servico'],
            nome_profissional=(servico.get('nome_profissional') or ordem.profissional_responsavel or '').strip(),
            valor_servico=servico.get('valor_servico', 0),
        )
        db.session.add(item)
        itens.append(item)
    db.session.flush()
    return itens


def substituir_servicos_da_ordem(ordem, servicos_payload: list[dict]):
    from models import ItemServico

    ItemServico.query.filter_by(ordem_id=ordem.id).delete()
    return anexar_servicos_em_ordem(ordem, servicos_payload)


def atualizar_profissional_dos_servicos(ordem):
    from models import ItemServico

    return ItemServico.query.filter_by(ordem_id=ordem.id).update(
        {'nome_profissional': ordem.profissional_responsavel}
    )


def duplicar_servicos_da_ordem(origem, nova_ordem):
    from models import ItemServico

    itens = []
    for servico in origem.servicos:
        item = ItemServico(
            ordem_id=nova_ordem.id,
            codigo_servico=servico.codigo_servico,
            descricao_servico=servico.descricao_servico,
            nome_profissional=servico.nome_profissional or nova_ordem.profissional_responsavel or '',
            valor_servico=servico.valor_servico or 0,
        )
        db.session.add(item)
        itens.append(item)
    db.session.flush()
    return itens


def listar_servicos_com_filtro_periodo(data_inicio, data_fim):
    from sqlalchemy import func
    from models import ItemServico, Ordem

    data_ref_expr = func.coalesce(
        Ordem.data_conclusao,
        Ordem.data_emissao,
        Ordem.data_entrada,
    )
    profissional_expr = func.coalesce(
        func.nullif(func.trim(ItemServico.nome_profissional), ''),
        func.nullif(func.trim(Ordem.profissional_responsavel), ''),
        'Nao informado',
    )

    rows = (
        ItemServico.query
        .join(Ordem, ItemServico.ordem_id == Ordem.id)
        .with_entities(
            Ordem.id.label('ordem_id'),
            data_ref_expr.label('data_ref'),
            profissional_expr.label('profissional'),
            ItemServico.descricao_servico.label('descricao'),
            func.coalesce(ItemServico.valor_servico, 0.0).label('valor'),
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
        'profissional': row.profissional or 'Nao informado',
        'descricao': row.descricao or '---',
        'valor': float(row.valor or 0),
    } for row in rows]
