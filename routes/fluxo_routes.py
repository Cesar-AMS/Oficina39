# ===========================================
# routes/fluxo_routes.py - Rotas de Fluxo de Caixa
# ===========================================

from flask import Blueprint, request, jsonify
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func
from services.auditoria_service import registrar_evento_auditoria

fluxo_bp = Blueprint('fluxo', __name__, url_prefix='/api/fluxo')


def _periodo_por_data(data_str=None):
    if data_str:
        base = datetime.strptime(data_str, '%Y-%m-%d')
    else:
        base = datetime.now()
    inicio = base.replace(hour=0, minute=0, second=0, microsecond=0)
    fim = base.replace(hour=23, minute=59, second=59, microsecond=999999)
    return inicio, fim

# ===========================================
# DADOS DO PERÍODO (ENTRADAS E SAÍDAS)
# ===========================================
@fluxo_bp.route('/periodo', methods=['GET'])
def fluxo_periodo():
    """Retorna entradas e saídas do período solicitado (padrão: dia)."""
    try:
        print("="*50)
        print("ROTA FLUXO PERIODO")
        
        from models import Ordem, Cliente, Saida
        
        periodo = request.args.get('periodo', 'dia')
        print(f"Periodo: {periodo}")
        
        hoje = datetime.now()
        
        # Definir intervalo de datas baseado no período
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
            return jsonify({'erro': 'Período inválido'}), 400
        
        print(f"Data inicio: {data_inicio}")
        print(f"Data fim: {data_fim}")
        
        # Buscar ordens executadas no período (concluídas/garantia com data de conclusão/retirada no intervalo).
        ordens_concluidas = Ordem.query.filter(Ordem.status.in_(['Concluído', 'Garantia'])).all()
        print(f"Ordens elegiveis: {len(ordens_concluidas)}")
        
        entradas = []
        for o in ordens_concluidas:
            data_ordem = o.data_conclusao or o.data_retirada
            if data_ordem and data_inicio <= data_ordem <= data_fim:
                cliente = Cliente.query.get(o.cliente_id)
                entradas.append({
                    'id': o.id,
                    'data': data_ordem.strftime('%d/%m/%Y'),
                    'cliente_nome': cliente.nome_cliente if cliente else '---',
                    'veiculo': f"{cliente.fabricante or ''} {cliente.modelo or ''}".strip(),
                    'placa': cliente.placa if cliente else '---',
                    'total': float(o.total_geral or 0),
                    'status': o.status
                })
        
        print(f"Entradas no periodo: {len(entradas)}")
        
        # Buscar saídas estritamente dentro do período.
        # Usa DateTime completo para compatibilidade com o modelo atual.
        saidas_db = (
            Saida.query
            .filter(Saida.data >= data_inicio, Saida.data <= data_fim)
            .order_by(Saida.data.desc())
            .all()
        )
        saidas = []
        for s in saidas_db:
            saidas.append({
                'id': s.id,
                'data': s.data.strftime('%d/%m/%Y') if s.data else None,
                'descricao': s.descricao,
                'categoria': s.categoria or 'Outros',
                'valor': float(s.valor or 0)
            })
        
        print(f"Saidas no periodo: {len(saidas)}")
        print("="*50)
        
        return jsonify({
            'entradas': entradas,
            'saidas': saidas
        })
        
    except Exception as e:
        print(f"ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# CRIAR NOVA SAÍDA
# ===========================================
@fluxo_bp.route('/saidas', methods=['POST'])
def criar_saida():
    try:
        from models import Saida
        from datetime import datetime  # ← IMPORTANTE!
        
        dados = request.json
        print(f"Dados recebidos: {dados}")
        
        if not dados.get('descricao') or not dados.get('valor'):
            return jsonify({'erro': 'Descrição e valor são obrigatórios'}), 400
        
        # ⚠️ CORREÇÃO: converter string para data se existir
        data_recebida = dados.get('data')
        if data_recebida:
            # Converte string '2026-02-22' para objeto date
            data_obj = datetime.strptime(data_recebida, '%Y-%m-%d').date()
        else:
            data_obj = datetime.now().date()
        
        saida = Saida(
            descricao=dados['descricao'],
            valor=float(dados['valor']),
            data=data_obj,  # ← Agora é sempre um objeto date!
            categoria=dados.get('categoria', 'Outros')
        )
        
        db.session.add(saida)
        db.session.commit()
        
        return jsonify(saida.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# LISTAR SAÍDAS
# ===========================================
@fluxo_bp.route('/saidas', methods=['GET'])
def listar_saidas():
    try:
        from models import Saida
        saidas = Saida.query.order_by(Saida.data.desc()).all()
        return jsonify([s.to_dict() for s in saidas])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===========================================
# DELETAR SAÍDA
# ===========================================
@fluxo_bp.route('/saidas/<int:id>', methods=['DELETE'])
def deletar_saida(id):
    try:
        from models import Saida
        saida = Saida.query.get(id)
        if not saida:
            return jsonify({'erro': 'Saída não encontrada'}), 404

        registrar_evento_auditoria(
            acao='EXCLUSAO_SAIDA',
            entidade='saida',
            entidade_id=saida.id,
            valor_anterior=f'{float(saida.valor or 0):.2f}',
            valor_novo='0.00',
            observacao=f'{(saida.categoria or "Outros")}: {(saida.descricao or "")[:140]}',
            request_ctx=request
        )
        db.session.delete(saida)
        db.session.commit()
        
        return jsonify({'mensagem': 'Saída removida com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@fluxo_bp.route('/fechamento-conferencia', methods=['POST'])
def fechamento_conferencia():
    """
    Compara valor esperado x valor contado por forma de pagamento no dia.
    """
    try:
        from models import Ordem, Saida
        dados = request.json or {}
        data_ref = (dados.get('data') or '').strip()
        contagem = dados.get('contagem') or {}
        if not isinstance(contagem, dict):
            return jsonify({'erro': 'contagem deve ser um objeto.'}), 400

        data_inicio, data_fim = _periodo_por_data(data_ref)

        esperados_rows = (
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
        esperados = {row.forma_pagamento: float(row.valor_esperado or 0) for row in esperados_rows}

        # Mantem ordem previsivel e inclui formas adicionais vindas da contagem.
        ordem_formas = ['Pix', 'Cartão', 'Dinheiro', 'Boleto', 'Transferência', 'Não informado']
        formas_dict = {forma: True for forma in ordem_formas}
        for forma in list(esperados.keys()) + [k for k in contagem.keys()]:
            if forma not in formas_dict:
                formas_dict[forma] = True
        formas = list(formas_dict.keys())
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

        total_saidas_rows = (
            Saida.query
            .with_entities(func.coalesce(func.sum(Saida.valor), 0.0))
            .filter(Saida.data >= data_inicio, Saida.data <= data_fim)
            .first()
        )
        total_saidas = float((total_saidas_rows[0] if total_saidas_rows else 0) or 0)

        return jsonify({
            'data': data_inicio.strftime('%Y-%m-%d'),
            'comparativo': comparativo,
            'total_esperado': total_esperado,
            'total_contado': total_contado,
            'diferenca_total': total_contado - total_esperado,
            'total_saidas': total_saidas,
            'saldo_estimado': total_esperado - total_saidas
        })
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD.'}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

