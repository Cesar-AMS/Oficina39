from sqlalchemy import func, or_

from models import Cliente, Ordem, OrdemAnexo, OrdemStatusLog, Profissional


def listar_todas():
    return Ordem.query.order_by(Ordem.id.desc()).all()


def buscar_por_id(ordem_id):
    return Ordem.query.get(ordem_id)


def listar_logs_status(ordem_id):
    return OrdemStatusLog.query.filter_by(ordem_id=ordem_id).order_by(OrdemStatusLog.data_evento.desc()).all()


def listar_anexos(ordem_id):
    return OrdemAnexo.query.filter_by(ordem_id=ordem_id).order_by(OrdemAnexo.created_at.desc()).all()


def buscar_anexo(ordem_id, anexo_id):
    return OrdemAnexo.query.filter_by(id=anexo_id, ordem_id=ordem_id).first()


def profissional_ativo_existe(nome_profissional):
    nome = (nome_profissional or '').strip()
    if not nome:
        return False
    profissional = (
        Profissional.query
        .filter(func.lower(Profissional.nome) == nome.lower())
        .filter(Profissional.ativo.is_(True))
        .first()
    )
    return profissional is not None


def buscar_por_filtros(cliente=None, status=None, profissional=None, forma_pagamento=None, data_inicio=None, data_fim=None):
    query = Ordem.query

    if cliente:
        termo = cliente.strip()
        termo_numerico = ''.join(ch for ch in termo if ch.isdigit())
        cpf_sem_mascara = func.replace(func.replace(func.replace(Cliente.cpf, '.', ''), '-', ''), '/', '')

        condicoes = [
            Cliente.nome_cliente.ilike(f'%{termo}%'),
            Cliente.cpf.ilike(f'%{termo}%')
        ]
        if termo_numerico:
            condicoes.append(cpf_sem_mascara.ilike(f'%{termo_numerico}%'))

        clientes = Cliente.query.filter(or_(*condicoes)).all()
        ids_clientes = [c.id for c in clientes]
        if ids_clientes:
            query = query.filter(Ordem.cliente_id.in_(ids_clientes))
        else:
            return []

    if status:
        query = query.filter(Ordem.status == status)
    if profissional:
        query = query.filter(Ordem.profissional_responsavel.ilike(f'%{profissional}%'))
    if forma_pagamento:
        query = query.filter(Ordem.forma_pagamento == forma_pagamento)
    if data_inicio:
        query = query.filter(Ordem.data_entrada >= data_inicio)
    if data_fim:
        query = query.filter(Ordem.data_entrada <= data_fim)

    return query.order_by(Ordem.id.desc()).all()


def listar_concluidas_por_periodo(data_inicio, data_fim):
    return Ordem.query.filter(Ordem.status.in_(['Concluído', 'Garantia'])).filter(
        Ordem.data_conclusao >= data_inicio,
        Ordem.data_conclusao <= data_fim
    ).all()


def somatorio_por_forma_pagamento(data_inicio, data_fim):
    return (
        Ordem.query
        .with_entities(
            func.coalesce(func.nullif(func.trim(Ordem.forma_pagamento), ''), 'Não informado').label('forma_pagamento'),
            func.coalesce(func.sum(Ordem.total_geral), 0.0).label('valor_esperado')
        )
        .filter(Ordem.status.in_(['Concluído', 'Garantia']))
        .filter(Ordem.data_conclusao >= data_inicio, Ordem.data_conclusao <= data_fim)
        .group_by('forma_pagamento')
        .all()
    )
