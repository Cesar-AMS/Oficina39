from __future__ import annotations

from flask import Blueprint, jsonify, request

from extensions import db
from services.peca_service import (
    atualizar_peca,
    baixar_estoque,
    criar_peca,
    excluir_peca,
    listar_pecas,
    obter_peca,
    repor_estoque,
)


pecas_bp = Blueprint('pecas', __name__, url_prefix='/api/pecas')


@pecas_bp.route('', methods=['GET'])
@pecas_bp.route('/', methods=['GET'])
def listar():
    try:
        pagina = request.args.get('pagina', 1, type=int)
        limite = request.args.get('limite', 20, type=int)
        filtros = {
            'nome': request.args.get('nome', ''),
            'categoria': request.args.get('categoria', ''),
        }
        resultado = listar_pecas(filtros=filtros, pagina=pagina, limite=limite)
        return jsonify(resultado)
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@pecas_bp.route('/<int:id>', methods=['GET'])
def obter(id):
    try:
        peca = obter_peca(id)
        return jsonify(peca.to_dict())
    except LookupError as exc:
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@pecas_bp.route('', methods=['POST'])
@pecas_bp.route('/', methods=['POST'])
def criar():
    try:
        peca = criar_peca(request.json or {})
        return jsonify(peca.to_dict()), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@pecas_bp.route('/<int:id>', methods=['PUT'])
def atualizar(id):
    try:
        peca = atualizar_peca(id, request.json or {})
        return jsonify(peca.to_dict())
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@pecas_bp.route('/<int:id>', methods=['DELETE'])
def excluir(id):
    try:
        excluir_peca(id)
        return jsonify({'mensagem': 'Peca excluida com sucesso.'})
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@pecas_bp.route('/<int:id>/estoque', methods=['PATCH'])
def movimentar_estoque(id):
    try:
        dados = request.json or {}
        operacao = (dados.get('operacao') or '').strip().lower()
        quantidade = dados.get('quantidade')

        if operacao == 'baixar':
            peca = baixar_estoque(id, quantidade)
        elif operacao == 'repor':
            peca = repor_estoque(id, quantidade)
        else:
            return jsonify({'erro': 'Operacao invalida. Use baixar ou repor.'}), 400

        return jsonify(peca.to_dict())
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500
