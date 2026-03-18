from flask import Blueprint, jsonify

from services.integration_service import consultar_cep, consultar_placa

integracoes_bp = Blueprint('integracoes', __name__, url_prefix='/api/integracoes')


@integracoes_bp.route('/cep/<string:cep>', methods=['GET'])
def buscar_cep(cep):
    try:
        return jsonify(consultar_cep(cep))
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@integracoes_bp.route('/placa/<string:placa>', methods=['GET'])
def buscar_placa(placa):
    try:
        return jsonify(consultar_placa(placa))
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
