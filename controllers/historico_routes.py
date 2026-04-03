from flask import Blueprint, jsonify, request

from services.historico_service import obter_historico_unificado


historico_bp = Blueprint('historico', __name__, url_prefix='/api/historico')


@historico_bp.route('/unificado', methods=['GET'])
def historico_unificado():
    try:
        entidade_tipo = request.args.get('entidade_tipo')
        entidade_id = request.args.get('entidade_id')
        limite = request.args.get('limite', '100')
        historico = obter_historico_unificado(
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            limite=limite,
        )
        return jsonify(historico)
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
