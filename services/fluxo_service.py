from datetime import datetime, timedelta

from extensions import db
from models import Saida
from repositories import ordem_repository, saida_repository


def periodo_por_data(data_str=None):
    if data_str:
        base = datetime.strptime(data_str, '%Y-%m-%d')
    else:
        base = datetime.now()
    inicio = base.replace(hour=0, minute=0, second=0, microsecond=0)
    fim = base.replace(hour=23, minute=59, second=59, microsecond=999999)
    return inicio, fim


def resolver_intervalo_periodo(periodo):
    hoje = datetime.now()
    if periodo == 'dia':
        data_inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
        data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif periodo == 'semana':
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        data_inicio = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
        data_fim = data_inicio + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
    elif periodo == 'mes':
        data_inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if hoje.month == 12:
            prox_mes = hoje.replace(year=hoje.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            prox_mes = hoje.replace(month=hoje.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        data_fim = prox_mes - timedelta(microseconds=1)
    else:
        raise ValueError('Período inválido')
    return data_inicio, data_fim


def obter_fluxo_periodo(periodo):
    data_inicio, data_fim = resolver_intervalo_periodo(periodo)
    ordens_concluidas = ordem_repository.listar_concluidas_por_periodo(data_inicio, data_fim)
    entradas = []
    for ordem in ordens_concluidas:
        cliente = ordem.cliente
        data_ordem = ordem.data_conclusao or ordem.data_retirada
        if data_ordem:
            entradas.append({
                'id': ordem.id,
                'data': data_ordem.strftime('%d/%m/%Y'),
                'cliente_nome': cliente.nome_cliente if cliente else '---',
                'veiculo': f"{cliente.fabricante or ''} {cliente.modelo or ''}".strip() if cliente else '',
                'placa': cliente.placa if cliente else '---',
                'total': float(ordem.total_geral or 0),
                'status': ordem.status
            })

    saidas = [{
        'id': s.id,
        'data': s.data.strftime('%d/%m/%Y') if s.data else None,
        'descricao': s.descricao,
        'categoria': s.categoria or 'Outros',
        'valor': float(s.valor or 0)
    } for s in saida_repository.listar_por_periodo(data_inicio, data_fim)]

    return {'entradas': entradas, 'saidas': saidas}


def criar_saida(dados):
    if not dados.get('descricao') or not dados.get('valor'):
        raise ValueError('Descrição e valor são obrigatórios')

    data_recebida = dados.get('data')
    if data_recebida:
        data_obj = datetime.strptime(data_recebida, '%Y-%m-%d')
    else:
        data_obj = datetime.now()

    saida = Saida(
        descricao=dados['descricao'],
        valor=float(dados['valor']),
        data=data_obj,
        categoria=dados.get('categoria', 'Outros')
    )
    db.session.add(saida)
    db.session.commit()
    return saida


def fechamento_conferencia(dados):
    data_ref = (dados.get('data') or '').strip()
    contagem = dados.get('contagem') or {}
    if not isinstance(contagem, dict):
        raise TypeError('contagem deve ser um objeto.')

    data_inicio, data_fim = periodo_por_data(data_ref)
    esperados_rows = ordem_repository.somatorio_por_forma_pagamento(data_inicio, data_fim)
    esperados = {row.forma_pagamento: float(row.valor_esperado or 0) for row in esperados_rows}

    ordem_formas = ['Pix', 'Cartão', 'Dinheiro', 'Boleto', 'Transferência', 'Não informado']
    formas_dict = {forma: True for forma in ordem_formas}
    for forma in list(esperados.keys()) + list(contagem.keys()):
        if forma not in formas_dict:
            formas_dict[forma] = True

    comparativo = []
    total_esperado = 0.0
    total_contado = 0.0
    for forma in formas_dict.keys():
        esperado = float(esperados.get(forma, 0.0))
        contado = float(contagem.get(forma, 0.0) or 0.0)
        diferenca = contado - esperado
        comparativo.append({
            'forma_pagamento': forma,
            'valor_esperado': esperado,
            'valor_contado': contado,
            'diferenca': diferenca
        })
        total_esperado += esperado
        total_contado += contado

    total_saidas = saida_repository.somar_por_periodo(data_inicio, data_fim)

    return {
        'data': data_inicio.strftime('%Y-%m-%d'),
        'comparativo': comparativo,
        'total_esperado': total_esperado,
        'total_contado': total_contado,
        'diferenca_total': total_contado - total_esperado,
        'total_saidas': total_saidas,
        'saldo_estimado': total_esperado - total_saidas
    }
