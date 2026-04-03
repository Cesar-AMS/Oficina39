from __future__ import annotations

from flask import Blueprint, jsonify, request

from extensions import db
from .auth_utils import require_auth
from services.servico_service import (
    atualizar_servico,
    buscar_por_nome,
    criar_servico,
    excluir_servico,
    listar_servicos,
    obter_servico,
)


servicos_bp = Blueprint('servicos', __name__, url_prefix='/api/servicos')


@servicos_bp.route('', methods=['GET'])
@servicos_bp.route('/', methods=['GET'])
def listar():
    try:
        pagina = request.args.get('pagina', 1, type=int)
        limite = request.args.get('limite', 20, type=int)
        filtros = {
            'nome': request.args.get('nome', ''),
            'categoria': request.args.get('categoria', ''),
        }
        resultado = listar_servicos(filtros=filtros, pagina=pagina, limite=limite)
        return jsonify(resultado)
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@servicos_bp.route('/buscar', methods=['GET'])
def buscar_nome():
    try:
        nome = request.args.get('nome', '')
        itens = buscar_por_nome(nome)
        return jsonify([item.to_dict() for item in itens])
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@servicos_bp.route('/<int:id>', methods=['GET'])
def obter(id):
    try:
        servico = obter_servico(id)
        return jsonify(servico.to_dict())
    except LookupError as exc:
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@servicos_bp.route('', methods=['POST'])
@servicos_bp.route('/', methods=['POST'])
@require_auth
def criar():
    try:
        servico = criar_servico(request.json or {})
        return jsonify(servico.to_dict()), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@servicos_bp.route('/<int:id>', methods=['PUT'])
@require_auth
def atualizar(id):
    try:
        servico = atualizar_servico(id, request.json or {})
        return jsonify(servico.to_dict())
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@servicos_bp.route('/<int:id>', methods=['DELETE'])
@require_auth
def excluir(id):
    try:
        excluir_servico(id)
        return jsonify({'mensagem': 'Servico excluido com sucesso.'})
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500
