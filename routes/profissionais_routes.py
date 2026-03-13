# ===========================================
# routes/profissionais_routes.py
# ===========================================

from flask import Blueprint, jsonify, request
from extensions import db

profissionais_bp = Blueprint('profissionais', __name__, url_prefix='/api/profissionais')


@profissionais_bp.route('/', methods=['GET'])
def listar_profissionais():
    try:
        from models import Profissional
        ativos_apenas = request.args.get('ativos', '1') == '1'
        query = Profissional.query
        if ativos_apenas:
            query = query.filter(Profissional.ativo.is_(True))
        profissionais = query.order_by(Profissional.nome.asc()).all()
        return jsonify([p.to_dict() for p in profissionais])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@profissionais_bp.route('/', methods=['POST'])
def criar_profissional():
    try:
        from models import Profissional
        dados = request.json or {}
        nome = (dados.get('nome') or '').strip()
        cnpj = (dados.get('cnpj') or '').strip()

        if not nome or not cnpj:
            return jsonify({'erro': 'Nome e CNPJ são obrigatórios.'}), 400

        existe_nome = Profissional.query.filter(Profissional.nome == nome).first()
        if existe_nome:
            return jsonify({'erro': 'Já existe profissional com este nome.'}), 400

        existe_cnpj = Profissional.query.filter(Profissional.cnpj == cnpj).first()
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
        from models import Profissional
        profissional = Profissional.query.get(id)
        if not profissional:
            return jsonify({'erro': 'Profissional não encontrado.'}), 404

        dados = request.json or {}
        nome = (dados.get('nome') or profissional.nome).strip()
        cnpj = (dados.get('cnpj') or profissional.cnpj).strip()

        outro_nome = Profissional.query.filter(Profissional.nome == nome, Profissional.id != id).first()
        if outro_nome:
            return jsonify({'erro': 'Já existe profissional com este nome.'}), 400

        outro_cnpj = Profissional.query.filter(Profissional.cnpj == cnpj, Profissional.id != id).first()
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
        from models import Profissional
        profissional = Profissional.query.get(id)
        if not profissional:
            return jsonify({'erro': 'Profissional não encontrado.'}), 404

        db.session.delete(profissional)
        db.session.commit()
        return jsonify({'mensagem': 'Profissional removido com sucesso.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500
