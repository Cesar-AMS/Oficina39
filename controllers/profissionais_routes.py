from flask import Blueprint, jsonify, request, send_file

from extensions import db
from .auth_utils import require_auth
from repositories import profissional_repository
from services.anexo_service import excluir_anexo, listar_anexos, obter_anexo, resolver_caminho_absoluto, salvar_anexo
from utils.formatters import cnpj_sem_mascara, texto_limpo


profissionais_bp = Blueprint('profissionais', __name__, url_prefix='/api/profissionais')


@profissionais_bp.route('/', methods=['GET'])
def listar_profissionais():
    try:
        ativos_apenas = request.args.get('ativos', '1') == '1'
        profissionais = profissional_repository.listar(ativos_apenas=ativos_apenas)
        return jsonify([p.to_dict() for p in profissionais])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@profissionais_bp.route('/', methods=['POST'])
@require_auth
def criar_profissional():
    try:
        from models import Profissional

        dados = request.json or {}
        nome = texto_limpo(dados.get('nome'))
        cnpj = cnpj_sem_mascara(dados.get('cnpj'))

        if not nome or not cnpj:
            return jsonify({'erro': 'Nome e CNPJ sao obrigatorios.'}), 400

        if profissional_repository.buscar_por_nome(nome):
            return jsonify({'erro': 'Ja existe profissional com este nome.'}), 400

        if profissional_repository.buscar_por_cnpj(cnpj):
            return jsonify({'erro': 'Ja existe profissional com este CNPJ.'}), 400

        profissional = Profissional(
            nome=nome,
            cnpj=cnpj,
            ativo=bool(dados.get('ativo', True)),
        )
        db.session.add(profissional)
        db.session.commit()
        return jsonify(profissional.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@profissionais_bp.route('/<int:id>', methods=['PUT'])
@require_auth
def atualizar_profissional(id):
    try:
        profissional = profissional_repository.buscar_por_id(id)
        if not profissional:
            return jsonify({'erro': 'Profissional nao encontrado.'}), 404

        dados = request.json or {}
        nome = texto_limpo(dados.get('nome') or profissional.nome)
        cnpj = cnpj_sem_mascara(dados.get('cnpj') or profissional.cnpj)

        if profissional_repository.buscar_outro_por_nome(nome, id):
            return jsonify({'erro': 'Ja existe profissional com este nome.'}), 400
        if profissional_repository.buscar_outro_por_cnpj(cnpj, id):
            return jsonify({'erro': 'Ja existe profissional com este CNPJ.'}), 400

        profissional.nome = nome
        profissional.cnpj = cnpj
        if 'ativo' in dados:
            profissional.ativo = bool(dados.get('ativo'))

        db.session.commit()
        return jsonify(profissional.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@profissionais_bp.route('/<int:id>', methods=['DELETE'])
@require_auth
def deletar_profissional(id):
    try:
        profissional = profissional_repository.buscar_por_id(id)
        if not profissional:
            return jsonify({'erro': 'Profissional nao encontrado.'}), 404

        db.session.delete(profissional)
        db.session.commit()
        return jsonify({'mensagem': 'Profissional removido com sucesso.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@profissionais_bp.route('/<int:id>/anexos', methods=['GET'])
def listar_anexos_profissional(id):
    try:
        profissional = profissional_repository.buscar_por_id(id)
        if not profissional:
            return jsonify({'erro': 'Profissional nao encontrado.'}), 404
        anexos = listar_anexos('profissional', id)
        return jsonify([a.to_dict() for a in anexos])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@profissionais_bp.route('/<int:id>/anexos', methods=['POST'])
@require_auth
def upload_anexo_profissional(id):
    try:
        profissional = profissional_repository.buscar_por_id(id)
        if not profissional:
            return jsonify({'erro': 'Profissional nao encontrado.'}), 404
        anexo = salvar_anexo(
            entidade_tipo='profissional',
            entidade_id=id,
            arquivo=request.files.get('arquivo'),
            descricao=request.form.get('descricao'),
            categoria=request.form.get('categoria', 'documento'),
        )
        return jsonify(anexo.to_dict()), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@profissionais_bp.route('/<int:id>/anexos/<int:anexo_id>/download', methods=['GET'])
def download_anexo_profissional(id, anexo_id):
    try:
        profissional = profissional_repository.buscar_por_id(id)
        if not profissional:
            return jsonify({'erro': 'Profissional nao encontrado.'}), 404
        anexo = obter_anexo('profissional', id, anexo_id)
        if not anexo:
            return jsonify({'erro': 'Anexo nao encontrado.'}), 404
        caminho_abs = resolver_caminho_absoluto(anexo)
        return send_file(caminho_abs, as_attachment=True, download_name=getattr(anexo, 'nome_arquivo', None) or getattr(anexo, 'nome_original', 'anexo'))
    except FileNotFoundError as e:
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@profissionais_bp.route('/<int:id>/anexos/<int:anexo_id>', methods=['DELETE'])
@require_auth
def excluir_anexo_profissional(id, anexo_id):
    try:
        profissional = profissional_repository.buscar_por_id(id)
        if not profissional:
            return jsonify({'erro': 'Profissional nao encontrado.'}), 404
        excluir_anexo('profissional', id, anexo_id)
        return jsonify({'mensagem': 'Anexo removido com sucesso.'})
    except LookupError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500
