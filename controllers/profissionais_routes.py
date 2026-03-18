# ===========================================
# controllers/profissionais_routes.py
# ===========================================

from flask import Blueprint, jsonify, request
from extensions import db
from repositories import profissional_repository
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
def criar_profissional():
    try:
        from models import Profissional
        dados = request.json or {}
        nome = texto_limpo(dados.get('nome'))
        cnpj = cnpj_sem_mascara(dados.get('cnpj'))

        if not nome or not cnpj:
            return jsonify({'erro': 'Nome e CNPJ são obrigatórios.'}), 400

        existe_nome = profissional_repository.buscar_por_nome(nome)
        if existe_nome:
            return jsonify({'erro': 'Já existe profissional com este nome.'}), 400

        existe_cnpj = profissional_repository.buscar_por_cnpj(cnpj)
        if existe_cnpj:
            return jsonify({'erro': 'Já existe profissional com este CNPJ.'}), 400

        profissional = Profissional(
            nome=nome,
            cnpj=cnpj,
            ativo=bool(dados.get('ativo', True))
        )
        db.session.add(profissional)
        db.session.commit()
        return jsonify(profissional.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@profissionais_bp.route('/<int:id>', methods=['PUT'])
def atualizar_profissional(id):
    try:
        profissional = profissional_repository.buscar_por_id(id)
        if not profissional:
            return jsonify({'erro': 'Profissional não encontrado.'}), 404

        dados = request.json or {}
        nome = texto_limpo(dados.get('nome') or profissional.nome)
        cnpj = cnpj_sem_mascara(dados.get('cnpj') or profissional.cnpj)

        outro_nome = profissional_repository.buscar_outro_por_nome(nome, id)
        if outro_nome:
            return jsonify({'erro': 'Já existe profissional com este nome.'}), 400

        outro_cnpj = profissional_repository.buscar_outro_por_cnpj(cnpj, id)
        if outro_cnpj:
            return jsonify({'erro': 'Já existe profissional com este CNPJ.'}), 400

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
def deletar_profissional(id):
    try:
        profissional = profissional_repository.buscar_por_id(id)
        if not profissional:
            return jsonify({'erro': 'Profissional não encontrado.'}), 404

        db.session.delete(profissional)
        db.session.commit()
        return jsonify({'mensagem': 'Profissional removido com sucesso.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500
