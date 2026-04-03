from flask import Blueprint, jsonify

from .auth_utils import require_auth_or_api_key
from services.integration_service import consultar_cep, consultar_placa

integracoes_bp = Blueprint('integracoes', __name__, url_prefix='/api/integracoes')


@integracoes_bp.route('/status', methods=['GET'])
@require_auth_or_api_key('integracoes.leitura')
def status():
    return jsonify({'status': 'ok', 'servico': 'integracoes'})


@integracoes_bp.route('/cep/<string:cep>', methods=['GET'])
@require_auth_or_api_key('integracoes.leitura')
def buscar_cep(cep):
    try:
        return jsonify(consultar_cep(cep))
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@integracoes_bp.route('/placa/<string:placa>', methods=['GET'])
@require_auth_or_api_key('integracoes.leitura')
def buscar_placa(placa):
    try:
        return jsonify(consultar_placa(placa))
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
