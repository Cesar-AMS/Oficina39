from datetime import datetime, timedelta

from extensions import db
from models import OrdemPagamento, Saida
from repositories import saida_repository


FORMAS_PAGAMENTO_FECHAMENTO = ['Pix', 'Cartão', 'Dinheiro', 'Boleto', 'Não informado']


def _listar_pagamentos_periodo(data_inicio, data_fim):
    return (
        OrdemPagamento.query
        .join(OrdemPagamento.ordem)
        .filter(OrdemPagamento.data_pagamento >= data_inicio, OrdemPagamento.data_pagamento <= data_fim)
        .order_by(OrdemPagamento.data_pagamento.desc(), OrdemPagamento.id.desc())
        .all()
    )


def _veiculo_cliente(cliente):
    if not cliente:
        return ''
    return f"{cliente.fabricante or ''} {cliente.modelo or ''}".strip()


def _serializar_entrada_pagamento(pagamento):
    ordem = pagamento.ordem
    cliente = ordem.cliente if ordem else None
    pagamento_anterior = max(0.0, float((ordem.total_pago or 0)) - float(pagamento.valor or 0)) if ordem else 0.0
    origem = 'Recebimento de débito' if pagamento_anterior > 0.009 else 'Recebimento de OS'
    return {
        'id': pagamento.id,
        'ordem_id': ordem.id if ordem else None,
        'data': pagamento.data_pagamento.strftime('%d/%m/%Y'),
        'hora': pagamento.data_pagamento.strftime('%H:%M') if pagamento.data_pagamento else '--:--',
        'data_hora_iso': pagamento.data_pagamento.isoformat() if pagamento.data_pagamento else None,
        'tipo': 'Entrada',
        'origem': origem,
        'cliente_nome': cliente.nome_cliente if cliente else '---',
        'veiculo': _veiculo_cliente(cliente),
        'placa': cliente.placa if cliente else '---',
        'forma_pagamento': pagamento.forma_pagamento,
        'observacao': pagamento.observacao,
        'total': float(pagamento.valor or 0),
        'total_pago': float(ordem.total_pago or 0) if ordem else 0,
        'saldo_pendente': float(ordem.saldo_pendente or 0) if ordem else 0,
        'status_financeiro': ordem.status_financeiro if ordem else '---',
        'status': ordem.status if ordem else '---'
    }


def _serializar_saida(saida):
    return {
        'id': saida.id,
        'data': saida.data.strftime('%d/%m/%Y') if saida.data else None,
        'hora': saida.data.strftime('%H:%M') if saida.data else '--:--',
        'data_hora_iso': saida.data.isoformat() if saida.data else None,
        'tipo': 'Saída',
        'origem': 'Saída manual',
        'forma_pagamento': '---',
        'observacao': saida.descricao,
        'descricao': saida.descricao,
        'categoria': saida.categoria or 'Outros',
        'valor': float(saida.valor or 0)
    }


def _normalizar_valor_positivo(valor):
    valor_numerico = float(valor)
    if valor_numerico <= 0:
        raise ValueError('Valor deve ser maior que zero')
    return valor_numerico


def _parse_data_recebida(data_str):
    return datetime.strptime(data_str, '%Y-%m-%d') if data_str else datetime.now()


def _agrupar_valores_por_forma(pagamentos_periodo):
    esperados = {}
    for pagamento in pagamentos_periodo:
        forma = pagamento.forma_pagamento or 'Não informado'
        esperados[forma] = esperados.get(forma, 0.0) + float(pagamento.valor or 0)
    return esperados


def _formas_para_comparativo(esperados, contagem):
    formas = list(FORMAS_PAGAMENTO_FECHAMENTO)
    for forma in list(esperados.keys()) + list(contagem.keys()):
        if forma not in formas:
            formas.append(forma)
    return formas


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
    pagamentos_periodo = _listar_pagamentos_periodo(data_inicio, data_fim)
    entradas = [_serializar_entrada_pagamento(pagamento) for pagamento in pagamentos_periodo]
    saidas = [_serializar_saida(saida) for saida in saida_repository.listar_por_periodo(data_inicio, data_fim)]

    return {'entradas': entradas, 'saidas': saidas}


def criar_saida(dados):
    if not dados.get('descricao') or not dados.get('valor'):
        raise ValueError('Descrição e valor são obrigatórios')

    data_obj = _parse_data_recebida(dados.get('data'))
    valor = _normalizar_valor_positivo(dados['valor'])

    saida = Saida(
        descricao=dados['descricao'],
        valor=valor,
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
    pagamentos_periodo = _listar_pagamentos_periodo(data_inicio, data_fim)
    esperados = _agrupar_valores_por_forma(pagamentos_periodo)
    formas = _formas_para_comparativo(esperados, contagem)

    comparativo = []
    total_esperado = 0.0
    total_contado = 0.0
    for forma in formas:
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
