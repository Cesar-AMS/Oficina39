# ===========================================
# services/relatorio_service.py - Serviço de Relatórios
# ===========================================

from models import Ordem, Cliente, Saida
from datetime import datetime, timedelta

def buscar_dados_periodo(data_inicio):
    """
    Busca entradas e saídas de um período específico
    
    Args:
        data_inicio: Data de início do período
    
    Returns:
        tuple: (entradas, saidas, total_entradas, total_saidas, saldo)
    """
    # Buscar ordens concluídas
    ordens_concluidas = Ordem.query.filter(
        Ordem.status == 'Concluído'
    ).all()
    
    entradas = []
    total_entradas = 0
    
    for o in ordens_concluidas:
        if o.data_conclusao and o.data_conclusao.date() >= data_inicio.date():
            cliente = Cliente.query.get(o.cliente_id)
            entradas.append({
                'data': o.data_conclusao.strftime('%d/%m/%Y'),
                'cliente': cliente.nome_cliente if cliente else '---',
                'servico': o.diagnostico[:50] + '...' if o.diagnostico and len(o.diagnostico) > 50 else o.diagnostico or '---',
                'valor': o.total_geral,
                'pagamento': '---'
            })
            total_entradas += o.total_geral
    
    # Buscar saídas
    saidas_db = Saida.query.filter(Saida.data >= data_inicio.date()).all()
    saidas = []
    total_saidas = 0
    
    for s in saidas_db:
        saidas.append({
            'data': s.data.strftime('%d/%m/%Y') if s.data else None,
            'categoria': s.categoria or 'Outros',
            'descricao': s.descricao,
            'valor': s.valor
        })
        total_saidas += s.valor
    
    saldo = total_entradas - total_saidas
    
    return entradas, saidas, total_entradas, total_saidas, saldo


def gerar_relatorio_html(periodo, entradas, saidas, total_entradas, total_saidas, saldo):
    """
    Gera HTML do relatório para e-mail
    
    Args:
        periodo: Nome do período
        entradas: Lista de entradas
        saidas: Lista de saídas
        total_entradas: Total de entradas
        total_saidas: Total de saídas
        saldo: Saldo do período
    
    Returns:
        str: HTML formatado
    """
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
        <h1>📊 Relatório de Fluxo de Caixa</h1>
        <p><strong>Período:</strong> {periodo}</p>
        <p><strong>Data/Hora:</strong> {data_atual}</p>
        
        <div class="resumo">
            <h2>Resumo Financeiro</h2>
            <p><strong>Total de Entradas:</strong> R$ {total_entradas:.2f}</p>
            <p><strong>Total de Saídas:</strong> R$ {total_saidas:.2f}</p>
            <p><strong>Saldo:</strong> <span class="{'positivo' if saldo >=0 else 'negativo'}">R$ {saldo:.2f}</span></p>
        </div>
        
        <h2>📥 Entradas (Ordens Concluídas)</h2>
        <table>
            <tr>
                <th>Data</th>
                <th>Cliente</th>
                <th>Serviço</th>
                <th>Valor</th>
                <th>Pagamento</th>
            </tr>
    """
    
    if entradas:
        for e in entradas:
            html += f"""
            <tr>
                <td>{e['data']}</td>
                <td>{e['cliente']}</td>
                <td>{e['servico']}</td>
                <td>R$ {e['valor']:.2f}</td>
                <td>{e['pagamento']}</td>
            </tr>
            """
    else:
        html += """
            <tr>
                <td colspan="5" style="text-align: center; padding: 20px;">Nenhuma entrada no período</td>
            </tr>
        """
    
    html += f"""
        </table>
        
        <h2>📤 Saídas</h2>
        <table>
            <tr>
                <th>Data</th>
                <th>Categoria</th>
                <th>Descrição</th>
                <th>Valor</th>
            </tr>
    """
    
    if saidas:
        for s in saidas:
            html += f"""
            <tr>
                <td>{s['data']}</td>
                <td>{s['categoria']}</td>
                <td>{s['descricao']}</td>
                <td>R$ {s['valor']:.2f}</td>
            </tr>
            """
    else:
        html += """
            <tr>
                <td colspan="4" style="text-align: center; padding: 20px;">Nenhuma saída no período</td>
            </tr>
        """
    
    html += f"""
        </table>
        
        <div class="footer">
            <p>Relatório gerado automaticamente pelo Sistema de Gestão de Oficina</p>
            <p>© {datetime.now().year} - Todos os direitos reservados</p>
        </div>
    </body>
    </html>
    """
    
    return html


def calcular_dias_garantia(data_conclusao):
    """
    Calcula os dias restantes de garantia (90 dias)
    
    Args:
        data_conclusao: Data de conclusão da ordem
    
    Returns:
        int: Dias restantes (0 se expirado)
    """
    if not data_conclusao:
        return 0
    
    hoje = datetime.now().date()
    if isinstance(data_conclusao, datetime):
        conclusao = data_conclusao.date()
    else:
        conclusao = data_conclusao
    
    diff = (hoje - conclusao).days
    return max(0, 90 - diff)