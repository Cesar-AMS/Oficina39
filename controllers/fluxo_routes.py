# ===========================================
# controllers/fluxo_routes.py - Controller de Fluxo de Caixa
# ===========================================

from flask import Blueprint, request, jsonify
from extensions import db
from .auth_utils import require_profiles
from repositories import saida_repository
from services.auditoria_service import registrar_evento_auditoria
from services.fluxo_service import criar_saida as criar_saida_service
from services.fluxo_service import fechamento_conferencia as fechamento_conferencia_service
from services.fluxo_service import obter_fluxo_periodo

fluxo_bp = Blueprint('fluxo', __name__, url_prefix='/api/fluxo')

# ===========================================
# DADOS DO PERÍODO (ENTRADAS E SAÍDAS)
# ===========================================
@fluxo_bp.route('/periodo', methods=['GET'])
def fluxo_periodo():
    """Retorna entradas e saídas do período solicitado (padrão: dia)."""
    try:
        periodo = request.args.get('periodo', 'dia')
        return jsonify(obter_fluxo_periodo(periodo))
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===========================================
# CRIAR NOVA SAÍDA
# ===========================================
@fluxo_bp.route('/saidas', methods=['POST'])
@require_profiles('admin', 'gerente', 'operador')
def criar_saida():
    try:
        saida = criar_saida_service(request.json or {})
        return jsonify(saida.to_dict()), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# LISTAR SAÍDAS
# ===========================================
@fluxo_bp.route('/saidas', methods=['GET'])
def listar_saidas():
    try:
        saidas = saida_repository.listar_todas()
        return jsonify([s.to_dict() for s in saidas])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===========================================
# DELETAR SAÍDA
# ===========================================
@fluxo_bp.route('/saidas/<int:id>', methods=['DELETE'])
@require_profiles('admin', 'gerente')
def deletar_saida(id):
    try:
        saida = saida_repository.buscar_por_id(id)
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
@require_profiles('admin', 'gerente', 'operador')
def fechamento_conferencia():
    """
    Compara valor esperado x valor contado por forma de pagamento no dia.
    """
    try:
        return jsonify(fechamento_conferencia_service(request.json or {}))
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD.'}), 400
    except TypeError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

