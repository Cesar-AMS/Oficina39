from __future__ import annotations

from flask import Blueprint, jsonify, request

from extensions import db
from services.webhook_service import (
    atualizar_webhook,
    criar_webhook,
    desativar_webhook,
    disparar_evento_webhook,
    listar_webhooks,
    obter_webhook,
)
from .auth_utils import require_profiles


webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/webhooks')


@webhooks_bp.route('', methods=['GET'])
@webhooks_bp.route('/', methods=['GET'])
@require_profiles('admin', 'gerente')
def listar():
    try:
        filtros = {'evento': request.args.get('evento', '')}
        if 'ativo' in request.args:
            filtros['ativo'] = request.args.get('ativo')
        return jsonify([item.to_dict() for item in listar_webhooks(filtros)])
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@webhooks_bp.route('/<int:id>', methods=['GET'])
@require_profiles('admin', 'gerente')
def obter(id):
    try:
        return jsonify(obter_webhook(id).to_dict())
    except LookupError as exc:
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@webhooks_bp.route('', methods=['POST'])
@webhooks_bp.route('/', methods=['POST'])
@require_profiles('admin')
def criar():
    try:
        webhook = criar_webhook(request.json or {})
        return jsonify(webhook.to_dict()), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@webhooks_bp.route('/<int:id>', methods=['PUT'])
@require_profiles('admin')
def atualizar(id):
    try:
        webhook = atualizar_webhook(id, request.json or {})
        return jsonify(webhook.to_dict())
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@webhooks_bp.route('/<int:id>', methods=['DELETE'])
@require_profiles('admin')
def excluir(id):
    try:
        webhook = desativar_webhook(id)
        return jsonify(webhook.to_dict())
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@webhooks_bp.route('/disparar-teste', methods=['POST'])
@require_profiles('admin')
def disparar_teste():
    try:
        dados = request.json or {}
        evento = (dados.get('evento') or '').strip().lower()
        if not evento:
            return jsonify({'erro': 'Evento de teste e obrigatorio.'}), 400
        return jsonify(disparar_evento_webhook(evento, dados.get('payload') or {}))
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500
