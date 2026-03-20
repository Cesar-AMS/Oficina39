from flask import Blueprint, jsonify, request

from extensions import db
from services.debito_service import listar_debitos_abertos, registrar_pagamentos


debitos_bp = Blueprint('debitos', __name__, url_prefix='/api/debitos')


@debitos_bp.route('/', methods=['GET'])
def listar_debitos():
    try:
        ordens = listar_debitos_abertos()
        payload = []
        for ordem in ordens:
            dados = ordem.to_dict()
            dados['cliente'] = ordem.cliente.to_dict() if ordem.cliente else {}
            payload.append(dados)
        return jsonify(payload)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@debitos_bp.route('/<int:ordem_id>/pagamentos', methods=['POST'])
def receber_pagamentos(ordem_id):
    try:
        dados = request.json or {}
        ordem = registrar_pagamentos(ordem_id, dados.get('pagamentos', []), request)
        payload = ordem.to_dict()
        payload['cliente'] = ordem.cliente.to_dict() if ordem.cliente else {}
        return jsonify(payload)
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except LookupError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500
