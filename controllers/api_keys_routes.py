from __future__ import annotations

from flask import Blueprint, jsonify, request

from extensions import db
from services.api_key_service import (
    atualizar_api_key,
    criar_api_key,
    desativar_api_key,
    listar_api_keys,
    obter_api_key,
    rotacionar_secret,
)
from .auth_utils import require_profiles


api_keys_bp = Blueprint('api_keys', __name__, url_prefix='/api/api-keys')


@api_keys_bp.route('', methods=['GET'])
@api_keys_bp.route('/', methods=['GET'])
@require_profiles('admin')
def listar():
    try:
        filtros = {
            'termo': request.args.get('termo', ''),
        }
        if 'ativa' in request.args:
            filtros['ativa'] = request.args.get('ativa')
        return jsonify([item.to_dict() for item in listar_api_keys(filtros)])
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@api_keys_bp.route('/<int:id>', methods=['GET'])
@require_profiles('admin')
def obter(id):
    try:
        return jsonify(obter_api_key(id).to_dict())
    except LookupError as exc:
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@api_keys_bp.route('', methods=['POST'])
@api_keys_bp.route('/', methods=['POST'])
@require_profiles('admin')
def criar():
    try:
        api_key, secret = criar_api_key(request.json or {})
        return jsonify({
            'api_key': api_key.to_dict(),
            'secret': secret,
        }), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@api_keys_bp.route('/<int:id>', methods=['PUT'])
@require_profiles('admin')
def atualizar(id):
    try:
        api_key = atualizar_api_key(id, request.json or {})
        return jsonify(api_key.to_dict())
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@api_keys_bp.route('/<int:id>/rotacionar', methods=['PATCH'])
@require_profiles('admin')
def rotacionar(id):
    try:
        api_key, secret = rotacionar_secret(id)
        return jsonify({
            'api_key': api_key.to_dict(),
            'secret': secret,
        })
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@api_keys_bp.route('/<int:id>', methods=['DELETE'])
@require_profiles('admin')
def excluir(id):
    try:
        api_key = desativar_api_key(id)
        return jsonify(api_key.to_dict())
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500
