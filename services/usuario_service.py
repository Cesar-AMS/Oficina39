from __future__ import annotations

from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer

from extensions import db
from flask import current_app
from models import PERFIS_USUARIO, Usuario
from repositories import usuario_repository


def _normalizar_texto(valor: str | None) -> str:
    return (valor or '').strip()


def _normalizar_email(email: str | None) -> str:
    return _normalizar_texto(email).lower()


def _normalizar_perfil(perfil: str | None) -> str:
    valor = _normalizar_texto(perfil).lower() or 'operador'
    if valor not in PERFIS_USUARIO:
        raise ValueError('Perfil de usuario invalido.')
    return valor


def _serializer():
    secret = current_app.config.get('SECRET_KEY') or 'oficina39-secret'
    return URLSafeTimedSerializer(secret_key=secret, salt='auth-token')


def listar_usuarios(filtros: dict | None = None):
    filtros = filtros or {}
    ativo = filtros.get('ativo')
    if isinstance(ativo, str):
        ativo = ativo.strip().lower() in {'1', 'true', 'sim', 'yes'}
    return usuario_repository.listar(
        ativo=ativo if filtros.get('ativo') is not None else None,
        perfil=filtros.get('perfil'),
        termo=filtros.get('termo'),
    )


def obter_usuario(usuario_id: int) -> Usuario:
    usuario = usuario_repository.buscar_por_id(usuario_id)
    if not usuario:
        raise LookupError('Usuario nao encontrado.')
    return usuario


def criar_usuario(dados: dict) -> Usuario:
    nome = _normalizar_texto((dados or {}).get('nome'))
    email = _normalizar_email((dados or {}).get('email'))
    senha = _normalizar_texto((dados or {}).get('senha'))
    perfil = _normalizar_perfil((dados or {}).get('perfil'))
    ativo = bool((dados or {}).get('ativo', True))

    if not nome:
        raise ValueError('Nome do usuario e obrigatorio.')
    if not email:
        raise ValueError('E-mail do usuario e obrigatorio.')
    if not senha:
        raise ValueError('Senha do usuario e obrigatoria.')
    if usuario_repository.buscar_por_email(email):
        raise ValueError('Ja existe usuario com este e-mail.')

    usuario = Usuario(
        nome=nome,
        email=email,
        perfil=perfil,
        ativo=ativo,
    )
    usuario.definir_senha(senha)
    usuario_repository.criar(usuario)
    usuario_repository.salvar()
    return usuario


def atualizar_usuario(usuario_id: int, dados: dict) -> Usuario:
    usuario = obter_usuario(usuario_id)
    dados = dados or {}

    if 'nome' in dados:
        nome = _normalizar_texto(dados.get('nome'))
        if not nome:
            raise ValueError('Nome do usuario e obrigatorio.')
        usuario.nome = nome

    if 'email' in dados:
        email = _normalizar_email(dados.get('email'))
        if not email:
            raise ValueError('E-mail do usuario e obrigatorio.')
        existente = usuario_repository.buscar_por_email(email)
        if existente and existente.id != usuario.id:
            raise ValueError('Ja existe usuario com este e-mail.')
        usuario.email = email

    if 'perfil' in dados:
        usuario.perfil = _normalizar_perfil(dados.get('perfil'))

    if 'ativo' in dados:
        usuario.ativo = bool(dados.get('ativo'))

    usuario_repository.salvar()
    return usuario


def alterar_senha(usuario_id: int, senha_atual: str | None, nova_senha: str) -> Usuario:
    usuario = obter_usuario(usuario_id)
    nova_senha_limpa = _normalizar_texto(nova_senha)
    if not nova_senha_limpa:
        raise ValueError('Nova senha e obrigatoria.')
    if senha_atual is not None and usuario.senha_hash and not usuario.verificar_senha(senha_atual):
        raise ValueError('Senha atual invalida.')

    usuario.definir_senha(nova_senha_limpa)
    usuario_repository.salvar()
    return usuario


def autenticar_usuario(email: str, senha: str) -> Usuario:
    usuario = usuario_repository.buscar_por_email(email)
    if not usuario or not usuario.ativo or not usuario.verificar_senha(senha):
        raise ValueError('Credenciais invalidas.')
    usuario.registrar_acesso()
    usuario_repository.salvar()
    return usuario


def gerar_token(usuario: Usuario) -> str:
    return _serializer().dumps({
        'sub': usuario.id,
        'perfil': usuario.perfil,
        'email': usuario.email,
    })


def validar_token(token: str, max_age: int = 60 * 60 * 12) -> Usuario:
    if not token:
        raise ValueError('Token nao informado.')
    try:
        dados = _serializer().loads(token, max_age=max_age)
    except (BadSignature, BadTimeSignature):
        raise ValueError('Token invalido ou expirado.')

    usuario = obter_usuario(int(dados.get('sub')))
    if not usuario.ativo:
        raise ValueError('Usuario inativo.')
    return usuario


def garantir_admin_padrao():
    if usuario_repository.contar() > 0:
        return None

    senha_inicial = current_app.config.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
    usuario = Usuario(
        nome='Administrador',
        email='admin@oficina39.local',
        perfil='admin',
        ativo=True,
    )
    usuario.definir_senha(senha_inicial)
    usuario_repository.criar(usuario)
    usuario_repository.salvar()
    return usuario
