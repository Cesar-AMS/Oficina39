from datetime import datetime, timedelta

from sqlalchemy import func

from models import Cliente, ItemServico, Ordem, Profissional


def resolver_profissional_ativo(nome_informado):
    nome = (nome_informado or '').strip()
    if not nome:
        return None
    return (
        Profissional.query
        .filter(Profissional.ativo.is_(True))
        .filter(func.lower(Profissional.nome) == nome.lower())
        .first()
    )


def listar_profissionais_ativos(termo='', limite=100):
    query = Profissional.query.filter(Profissional.ativo.is_(True))
    if termo:
        query = query.filter(Profissional.nome.ilike(f'%{termo}%'))
    return query.order_by(Profissional.nome.asc()).limit(limite).all()


def total_profissionais_ativos():
    return Profissional.query.filter(Profissional.ativo.is_(True)).count()


def base_producao_query(data_inicio=None, data_fim=None):
    profissional_expr = func.coalesce(
        func.nullif(func.trim(ItemServico.nome_profissional), ''),
        func.nullif(func.trim(Ordem.profissional_responsavel), ''),
        'Nao informado'
    )

    data_ref_expr = func.coalesce(
        Ordem.data_conclusao,
        Ordem.data_retirada,
        Ordem.data_emissao,
        Ordem.data_entrada
    )

    query = ItemServico.query.join(Ordem, ItemServico.ordem_id == Ordem.id)
    if data_inicio:
        query = query.filter(data_ref_expr >= data_inicio)
    if data_fim:
        query = query.filter(data_ref_expr <= data_fim)

    return query, profissional_expr, data_ref_expr


def periodo_inicio_fim(data_ref, tipo):
    base = data_ref.replace(hour=0, minute=0, second=0, microsecond=0)
    if tipo == 'dia':
        inicio = base
        fim = base.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif tipo == 'semana':
        inicio = (base - timedelta(days=base.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        fim = inicio + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
    elif tipo == 'mes':
        inicio = base.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if inicio.month == 12:
            prox = inicio.replace(year=inicio.year + 1, month=1, day=1)
        else:
            prox = inicio.replace(month=inicio.month + 1, day=1)
        fim = prox - timedelta(microseconds=1)
    else:
        raise ValueError('Periodo inválido')
    return inicio, fim


def detalhes_resumo_profissional(profissional_nome, data_inicio, data_fim, limite=100):
    query_base, profissional_expr, data_ref_expr = base_producao_query(data_inicio, data_fim)
    query_base = query_base.filter(func.lower(profissional_expr) == profissional_nome.lower())

    resumo_row = query_base.with_entities(
        func.count(ItemServico.id),
        func.coalesce(func.sum(ItemServico.valor_servico), 0.0),
        func.coalesce(func.avg(ItemServico.valor_servico), 0.0)
    ).first()

    detalhes_rows = (
        query_base
        .with_entities(
            Ordem.id.label('ordem_id'),
            data_ref_expr.label('data_referencia'),
            Cliente.nome_cliente.label('cliente'),
            ItemServico.descricao_servico,
            ItemServico.valor_servico
        )
        .join(Cliente, Ordem.cliente_id == Cliente.id)
        .order_by(data_ref_expr.desc())
        .limit(limite)
        .all()
    )

    return {
        'resumo': {
            'quantidade_servicos': int((resumo_row[0] if resumo_row else 0) or 0),
            'valor_total': float((resumo_row[1] if resumo_row else 0) or 0),
            'media_por_servico': float((resumo_row[2] if resumo_row else 0) or 0),
        },
        'servicos': [{
            'ordem_id': row.ordem_id,
            'data_referencia': row.data_referencia.strftime('%d/%m/%Y') if row.data_referencia else '---',
            'cliente': row.cliente or '---',
            'descricao_servico': row.descricao_servico or '---',
            'valor_servico': float(row.valor_servico or 0)
        } for row in detalhes_rows]
    }
