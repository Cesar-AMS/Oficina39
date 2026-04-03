from __future__ import annotations

from flask import Blueprint, jsonify, request

from extensions import db
from .auth_utils import require_profiles
from services.comunicacao_service import (
    criar_comunicacao,
    listar_comunicacoes,
    obter_comunicacao,
    processar_comunicacao,
    processar_pendentes,
)
from services.template_comunicacao_service import (
    atualizar_template,
    criar_template,
    listar_templates,
    obter_template,
)


comunicacoes_bp = Blueprint('comunicacoes', __name__, url_prefix='/api/comunicacoes')


@comunicacoes_bp.route('', methods=['GET'])
@comunicacoes_bp.route('/', methods=['GET'])
@require_profiles('admin', 'gerente')
def listar():
    try:
        filtros = {
            'canal': request.args.get('canal', ''),
            'status': request.args.get('status', ''),
            'entidade_tipo': request.args.get('entidade_tipo', ''),
            'entidade_id': request.args.get('entidade_id'),
        }
        pagina = request.args.get('pagina', 1, type=int)
        limite = request.args.get('limite', 20, type=int)
        return jsonify(listar_comunicacoes(filtros, pagina=pagina, limite=limite))
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@comunicacoes_bp.route('/<int:id>', methods=['GET'])
@require_profiles('admin', 'gerente')
def obter(id):
    try:
        return jsonify(obter_comunicacao(id).to_dict())
    except LookupError as exc:
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@comunicacoes_bp.route('', methods=['POST'])
@comunicacoes_bp.route('/', methods=['POST'])
@require_profiles('admin', 'gerente')
def criar():
    try:
        processar_agora = bool((request.json or {}).get('processar_agora'))
        comunicacao = criar_comunicacao(request.json or {}, processar_agora=processar_agora)
        return jsonify(comunicacao.to_dict()), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@comunicacoes_bp.route('/<int:id>/processar', methods=['POST'])
@require_profiles('admin', 'gerente')
def processar(id):
    try:
        comunicacao = processar_comunicacao(id)
        return jsonify(comunicacao.to_dict())
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@comunicacoes_bp.route('/processar-pendentes', methods=['POST'])
@require_profiles('admin', 'gerente')
def processar_fila():
    try:
        limite = request.json.get('limite', 20) if isinstance(request.json, dict) else 20
        itens = processar_pendentes(limite=max(1, min(100, int(limite or 20))))
        return jsonify({
            'processadas': len(itens),
            'itens': [item.to_dict() for item in itens],
        })
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@comunicacoes_bp.route('/templates', methods=['GET'])
@require_profiles('admin', 'gerente')
def listar_templates_view():
    try:
        filtros = {
            'nome': request.args.get('nome', ''),
            'canal': request.args.get('canal', ''),
        }
        if 'ativo' in request.args:
            filtros['ativo'] = request.args.get('ativo')
        return jsonify([item.to_dict() for item in listar_templates(filtros)])
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@comunicacoes_bp.route('/templates', methods=['POST'])
@require_profiles('admin', 'gerente')
def criar_template_view():
    try:
        template = criar_template(request.json or {})
        return jsonify(template.to_dict()), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@comunicacoes_bp.route('/templates/<int:id>', methods=['GET'])
@require_profiles('admin', 'gerente')
def obter_template_view(id):
    try:
        return jsonify(obter_template(id).to_dict())
    except LookupError as exc:
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@comunicacoes_bp.route('/templates/<int:id>', methods=['PUT'])
@require_profiles('admin', 'gerente')
def atualizar_template_view(id):
    try:
        template = atualizar_template(id, request.json or {})
        return jsonify(template.to_dict())
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500
