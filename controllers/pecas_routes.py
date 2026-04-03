from __future__ import annotations

from flask import Blueprint, jsonify, request, send_file

from extensions import db
from .auth_utils import require_auth
from services.anexo_service import excluir_anexo, listar_anexos, obter_anexo, resolver_caminho_absoluto, salvar_anexo
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
@require_auth
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
@require_auth
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
@require_auth
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
@require_auth
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


@pecas_bp.route('/<int:id>/anexos', methods=['GET'])
def listar_anexos_peca(id):
    try:
        peca = obter_peca(id)
        anexos = listar_anexos('peca', id)
        return jsonify([a.to_dict() for a in anexos])
    except LookupError as exc:
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@pecas_bp.route('/<int:id>/anexos', methods=['POST'])
@require_auth
def upload_anexo_peca(id):
    try:
        obter_peca(id)
        anexo = salvar_anexo(
            entidade_tipo='peca',
            entidade_id=id,
            arquivo=request.files.get('arquivo'),
            descricao=request.form.get('descricao'),
            categoria=request.form.get('categoria', 'documento'),
        )
        return jsonify(anexo.to_dict()), 201
    except LookupError as exc:
        return jsonify({'erro': str(exc)}), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@pecas_bp.route('/<int:id>/anexos/<int:anexo_id>/download', methods=['GET'])
def download_anexo_peca(id, anexo_id):
    try:
        obter_peca(id)
        anexo = obter_anexo('peca', id, anexo_id)
        if not anexo:
            return jsonify({'erro': 'Anexo nao encontrado.'}), 404
        caminho_abs = resolver_caminho_absoluto(anexo)
        return send_file(caminho_abs, as_attachment=True, download_name=getattr(anexo, 'nome_arquivo', None) or getattr(anexo, 'nome_original', 'anexo'))
    except LookupError as exc:
        return jsonify({'erro': str(exc)}), 404
    except FileNotFoundError as exc:
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@pecas_bp.route('/<int:id>/anexos/<int:anexo_id>', methods=['DELETE'])
@require_auth
def excluir_anexo_peca(id, anexo_id):
    try:
        obter_peca(id)
        excluir_anexo('peca', id, anexo_id)
        return jsonify({'mensagem': 'Anexo removido com sucesso.'})
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500
