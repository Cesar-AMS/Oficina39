from datetime import datetime

from models import Ordem
from services import peca_service, servico_service
from services.caixa_service import obter_extrato


STATUS_CONCLUIDOS_RELATORIO = {'Concluído', 'Garantia'}


def relatorio_financeiro(data_inicio, data_fim):
    movimentos = obter_extrato(data_inicio, data_fim)
    detalhes = []
    total_entradas = 0.0
    total_saidas = 0.0
    pagamentos = {}

    for movimento in movimentos:
        valor = float(movimento.valor or 0)
        if (movimento.tipo or '').lower() == 'entrada':
            total_entradas += valor
            forma = _rotulo_forma_pagamento(movimento.forma_pagamento)
            bucket = pagamentos.setdefault(forma, {'forma_pagamento': forma, 'valor_total': 0.0, 'quantidade': 0})
            bucket['valor_total'] += valor
            bucket['quantidade'] += 1
        else:
            total_saidas += valor

        detalhes.append({
            'id': movimento.id,
            'tipo': movimento.tipo,
            'categoria': movimento.categoria,
            'valor': valor,
            'data_movimento': movimento.data_movimento.strftime('%Y-%m-%d %H:%M:%S') if movimento.data_movimento else None,
            'descricao': movimento.descricao,
            'forma_pagamento': _rotulo_forma_pagamento(movimento.forma_pagamento),
            'ordem_id': movimento.ordem_id,
            'cliente_id': movimento.cliente_id,
        })

    pagamentos_ordenados = sorted(
        (
            {
                'forma_pagamento': item['forma_pagamento'],
                'valor_total': round(item['valor_total'], 2),
                'quantidade': int(item['quantidade']),
            }
            for item in pagamentos.values()
        ),
        key=lambda item: item['valor_total'],
        reverse=True,
    )

    quantidade_os = (
        Ordem.query
        .filter(Ordem.status.in_(STATUS_CONCLUIDOS_RELATORIO))
        .filter(Ordem.data_conclusao >= data_inicio, Ordem.data_conclusao <= data_fim)
        .count()
    )

    return {
        'periodo': {
            'inicio': data_inicio.strftime('%Y-%m-%d'),
            'fim': data_fim.strftime('%Y-%m-%d'),
        },
        'faturamento_bruto': round(total_entradas, 2),
        'total_saidas': round(total_saidas, 2),
        'saldo_operacional': round(total_entradas - total_saidas, 2),
        'quantidade_os': int(quantidade_os or 0),
        'ticket_medio': round((total_entradas / quantidade_os), 2) if quantidade_os else 0.0,
        'pagamentos': pagamentos_ordenados,
        'detalhes': detalhes,
    }


def painel_dia_operacional(data_inicio, data_fim):
    ordens_abertas = (
        Ordem.query
        .filter(~Ordem.status.in_(list(STATUS_CONCLUIDOS_RELATORIO)))
        .count()
    )
    concluidas_hoje = (
        Ordem.query
        .filter(Ordem.status.in_(STATUS_CONCLUIDOS_RELATORIO))
        .filter(Ordem.data_conclusao >= data_inicio, Ordem.data_conclusao <= data_fim)
        .count()
    )

    relatorio = relatorio_financeiro(data_inicio, data_fim)
    return {
        'data': data_inicio.strftime('%Y-%m-%d'),
        'ordens_abertas': int(ordens_abertas or 0),
        'ordens_concluidas_hoje': int(concluidas_hoje or 0),
        'faturamento_hoje': relatorio['faturamento_bruto'],
        'saidas_hoje': relatorio['total_saidas'],
        'saldo_hoje': relatorio['saldo_operacional'],
    }


def relatorio_operacional(data_inicio, data_fim):
    servicos = servico_service.listar_servicos_com_filtro_periodo(data_inicio, data_fim)
    pecas = peca_service.listar_pecas_com_filtro_periodo(data_inicio, data_fim)
    movimentos_saida = obter_extrato(data_inicio, data_fim, tipo='saida')

    saidas = [{
        'data_referencia': movimento.data_movimento.strftime('%d/%m/%Y') if movimento.data_movimento else '---',
        'data_ordem': movimento.data_movimento.isoformat() if movimento.data_movimento else '',
        'categoria': movimento.categoria or 'Outros',
        'descricao': movimento.descricao or '---',
        'valor': float(movimento.valor or 0),
    } for movimento in movimentos_saida]

    return {
        'periodo': {
            'inicio': data_inicio.strftime('%Y-%m-%d'),
            'fim': data_fim.strftime('%Y-%m-%d'),
        },
        'servicos': servicos,
        'pecas': pecas,
        'saidas': saidas,
        'resumo': {
            'quantidade_servicos': len(servicos),
            'valor_servicos': round(sum(float(item['valor']) for item in servicos), 2),
            'quantidade_pecas': len(pecas),
            'valor_pecas': round(sum(float(item['valor_total']) for item in pecas), 2),
            'quantidade_saidas': len(saidas),
            'valor_saidas': round(sum(float(item['valor']) for item in saidas), 2),
        },
    }


def buscar_dados_periodo(data_inicio):
    data_fim = datetime.now()
    relatorio = relatorio_financeiro(data_inicio, data_fim)
    entradas = []
    saidas = []

    for item in relatorio['detalhes']:
        if item['tipo'] == 'entrada':
            entradas.append({
                'data': _formatar_data(item['data_movimento']),
                'cliente': '---',
                'servico': item['descricao'] or '---',
                'valor': item['valor'],
                'pagamento': item['forma_pagamento'] or '---',
            })
        else:
            saidas.append({
                'data': _formatar_data(item['data_movimento']),
                'categoria': item['categoria'] or 'Outros',
                'descricao': item['descricao'] or '---',
                'valor': item['valor'],
            })

    return (
        entradas,
        saidas,
        relatorio['faturamento_bruto'],
        relatorio['total_saidas'],
        relatorio['saldo_operacional'],
    )


def gerar_relatorio_html(periodo, entradas, saidas, total_entradas, total_saidas, saldo):
    data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #0a3147; border-bottom: 2px solid #c44536; padding-bottom: 10px; }}
            .resumo {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .positivo {{ color: #27ae60; font-weight: bold; }}
            .negativo {{ color: #e74c3c; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th {{ background: #0a3147; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
            tr:hover {{ background: #f9f9f9; }}
            .footer {{ margin-top: 30px; color: #999; font-size: 12px; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>Relatorio de Fluxo de Caixa</h1>
        <p><strong>Periodo:</strong> {periodo}</p>
        <p><strong>Data/Hora:</strong> {data_atual}</p>
        <div class="resumo">
            <h2>Resumo Financeiro</h2>
            <p><strong>Total de Entradas:</strong> R$ {total_entradas:.2f}</p>
            <p><strong>Total de Saidas:</strong> R$ {total_saidas:.2f}</p>
            <p><strong>Saldo:</strong> <span class="{'positivo' if saldo >= 0 else 'negativo'}">R$ {saldo:.2f}</span></p>
        </div>
        <h2>Entradas</h2>
        <table>
            <tr><th>Data</th><th>Cliente</th><th>Servico</th><th>Valor</th><th>Pagamento</th></tr>
    """

    if entradas:
        for e in entradas:
            html += f"<tr><td>{e['data']}</td><td>{e['cliente']}</td><td>{e['servico']}</td><td>R$ {e['valor']:.2f}</td><td>{e['pagamento']}</td></tr>"
    else:
        html += "<tr><td colspan='5' style='text-align:center;padding:20px;'>Nenhuma entrada no periodo</td></tr>"

    html += """
        </table>
        <h2>Saidas</h2>
        <table>
            <tr><th>Data</th><th>Categoria</th><th>Descricao</th><th>Valor</th></tr>
    """
    if saidas:
        for s in saidas:
            html += f"<tr><td>{s['data']}</td><td>{s['categoria']}</td><td>{s['descricao']}</td><td>R$ {s['valor']:.2f}</td></tr>"
    else:
        html += "<tr><td colspan='4' style='text-align:center;padding:20px;'>Nenhuma saida no periodo</td></tr>"

    html += f"""
        </table>
        <div class="footer">
            <p>Relatorio gerado automaticamente pelo Sistema de Gestao de Oficina</p>
            <p>&copy; {datetime.now().year} - Todos os direitos reservados</p>
        </div>
    </body>
    </html>
    """
    return html


def calcular_dias_garantia(data_conclusao):
    if not data_conclusao:
        return 0
    hoje = datetime.now().date()
    conclusao = data_conclusao.date() if isinstance(data_conclusao, datetime) else data_conclusao
    diff = (hoje - conclusao).days
    return max(0, 90 - diff)


def _rotulo_forma_pagamento(forma):
    mapping = {
        'pix': 'Pix',
        'dinheiro': 'Dinheiro',
        'cartao': 'Cartao',
        'debito_conta': 'Debito em conta',
        None: 'Nao informado',
        '': 'Nao informado',
    }
    return mapping.get(forma, str(forma).title() if forma else 'Nao informado')


def _formatar_data(data_hora):
    if not data_hora:
        return None
    try:
        ref = datetime.fromisoformat(data_hora)
    except ValueError:
        return data_hora
    return ref.strftime('%d/%m/%Y')
