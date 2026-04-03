from __future__ import annotations

from flask import Blueprint, jsonify, g, request

from extensions import db
from services.usuario_service import (
    alterar_senha,
    autenticar_usuario,
    criar_usuario,
    gerar_token,
    listar_usuarios,
    obter_usuario,
    atualizar_usuario,
)
from .auth_utils import require_auth, require_profiles


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/api/usuarios')


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        dados = request.json or {}
        usuario = autenticar_usuario(dados.get('email', ''), dados.get('senha', ''))
        return jsonify({
            'token': gerar_token(usuario),
            'usuario': usuario.to_dict(),
        })
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 401
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@auth_bp.route('/me', methods=['GET'])
@require_auth
def me():
    return jsonify(g.current_user.to_dict())


@usuarios_bp.route('', methods=['GET'])
@usuarios_bp.route('/', methods=['GET'])
@require_profiles('admin', 'gerente')
def listar():
    try:
        filtros = {
            'termo': request.args.get('termo', ''),
            'perfil': request.args.get('perfil', ''),
        }
        if 'ativo' in request.args:
            filtros['ativo'] = request.args.get('ativo')
        usuarios = listar_usuarios(filtros)
        return jsonify([usuario.to_dict() for usuario in usuarios])
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@usuarios_bp.route('/<int:id>', methods=['GET'])
@require_profiles('admin', 'gerente')
def obter(id):
    try:
        usuario = obter_usuario(id)
        return jsonify(usuario.to_dict())
    except LookupError as exc:
        return jsonify({'erro': str(exc)}), 404
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@usuarios_bp.route('', methods=['POST'])
@usuarios_bp.route('/', methods=['POST'])
@require_profiles('admin')
def criar():
    try:
        usuario = criar_usuario(request.json or {})
        return jsonify(usuario.to_dict()), 201
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@usuarios_bp.route('/<int:id>', methods=['PUT'])
@require_profiles('admin')
def atualizar(id):
    try:
        usuario = atualizar_usuario(id, request.json or {})
        return jsonify(usuario.to_dict())
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500


@usuarios_bp.route('/<int:id>/senha', methods=['PATCH'])
@require_auth
def alterar_senha_usuario(id):
    try:
        usuario_logado = g.current_user
        if usuario_logado.id != id and usuario_logado.perfil != 'admin':
            return jsonify({'erro': 'Acesso negado.'}), 403

        dados = request.json or {}
        senha_atual = None if usuario_logado.perfil == 'admin' and usuario_logado.id != id else dados.get('senha_atual')
        usuario = alterar_senha(id, senha_atual, dados.get('nova_senha', ''))
        return jsonify(usuario.to_dict())
    except LookupError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({'erro': str(exc)}), 500
