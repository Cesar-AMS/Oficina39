from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
import secrets

from flask import current_app
from itsdangerous import BadSignature, URLSafeSerializer

from models import ApiKey
from repositories import api_key_repository


_RATE_LIMIT_BUCKETS = defaultdict(deque)


def _texto(valor) -> str:
    return (valor or '').strip()


def _normalizar_bool(valor):
    if isinstance(valor, str):
        return valor.strip().lower() in {'1', 'true', 'sim', 'yes'}
    return bool(valor)


def _normalizar_permissoes(permissoes) -> list[str]:
    if permissoes is None:
        return []
    if not isinstance(permissoes, (list, tuple, set)):
        raise ValueError('Permissoes invalidas.')
    itens = []
    for item in permissoes:
        valor = _texto(item).lower()
        if valor:
            itens.append(valor)
    return sorted(set(itens))


def _normalizar_expiracao(valor):
    if valor in (None, ''):
        return None
    if isinstance(valor, datetime):
        return valor
    try:
        return datetime.fromisoformat(str(valor).strip())
    except ValueError as exc:
        raise ValueError('Data de expiracao invalida.') from exc


def _normalizar_rate_limit(valor) -> int:
    try:
        limite = int(valor if valor is not None else 100)
    except (TypeError, ValueError) as exc:
        raise ValueError('Rate limit invalido.') from exc
    if limite < 1:
        raise ValueError('Rate limit deve ser maior que zero.')
    return limite


def _gerar_chave() -> str:
    return secrets.token_hex(32)


def _gerar_secret() -> str:
    return secrets.token_urlsafe(32)


def _secret_serializer():
    secret = current_app.config.get('SECRET_KEY') or 'oficina39-secret'
    return URLSafeSerializer(secret_key=secret, salt='api-key-secret')


def _proteger_secret(secret: str) -> str:
    return _secret_serializer().dumps((secret or '').strip())


def _revelar_secret(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return str(_secret_serializer().loads(token))
    except BadSignature:
        return None


def listar_api_keys(filtros: dict | None = None):
    filtros = filtros or {}
    ativa = filtros.get('ativa')
    if ativa is not None:
        ativa = _normalizar_bool(ativa)
    return api_key_repository.listar(ativa=ativa, termo=filtros.get('termo'))


def obter_api_key(api_key_id: int) -> ApiKey:
    api_key = api_key_repository.buscar_por_id(api_key_id)
    if not api_key:
        raise LookupError('API key nao encontrada.')
    return api_key


def criar_api_key(dados: dict) -> tuple[ApiKey, str]:
    dados = dados or {}
    nome = _texto(dados.get('nome'))
    if not nome:
        raise ValueError('Nome da API key e obrigatorio.')

    api_key = ApiKey(
        nome=nome,
        key=_gerar_chave(),
        rate_limit=_normalizar_rate_limit(dados.get('rate_limit')),
        ativa=_normalizar_bool(dados.get('ativa', True)),
        expira_em=_normalizar_expiracao(dados.get('expira_em')),
    )
    api_key.permissoes = _normalizar_permissoes(dados.get('permissoes'))
    secret = _gerar_secret()
    api_key.definir_secret(secret)
    api_key.secret_token = _proteger_secret(secret)
    api_key_repository.criar(api_key)
    api_key_repository.salvar()
    return api_key, secret


def atualizar_api_key(api_key_id: int, dados: dict) -> ApiKey:
    api_key = obter_api_key(api_key_id)
    dados = dados or {}
    if 'nome' in dados:
        nome = _texto(dados.get('nome'))
        if not nome:
            raise ValueError('Nome da API key e obrigatorio.')
        api_key.nome = nome
    if 'permissoes' in dados:
        api_key.permissoes = _normalizar_permissoes(dados.get('permissoes'))
    if 'rate_limit' in dados:
        api_key.rate_limit = _normalizar_rate_limit(dados.get('rate_limit'))
    if 'ativa' in dados:
        api_key.ativa = _normalizar_bool(dados.get('ativa'))
    if 'expira_em' in dados:
        api_key.expira_em = _normalizar_expiracao(dados.get('expira_em'))
    api_key_repository.salvar()
    return api_key


def desativar_api_key(api_key_id: int) -> ApiKey:
    api_key = obter_api_key(api_key_id)
    api_key.ativa = False
    api_key_repository.salvar()
    return api_key


def rotacionar_secret(api_key_id: int) -> tuple[ApiKey, str]:
    api_key = obter_api_key(api_key_id)
    novo_secret = _gerar_secret()
    api_key.key = _gerar_chave()
    api_key.definir_secret(novo_secret)
    api_key.secret_token = _proteger_secret(novo_secret)
    api_key_repository.salvar()
    _RATE_LIMIT_BUCKETS.pop(api_key.id, None)
    return api_key, novo_secret


def obter_secret_api_key(api_key_id: int) -> str:
    api_key = obter_api_key(api_key_id)
    secret = _revelar_secret(api_key.secret_token)
    if not secret:
        raise ValueError('Secret da API key indisponivel.')
    return secret


def validar_api_key(chave: str, secret: str, permissoes: tuple[str, ...] | list[str] | None = None) -> ApiKey:
    api_key = api_key_repository.buscar_por_key(chave)
    if not api_key or not api_key.ativa:
        raise ValueError('API key invalida.')
    if api_key.expirada():
        raise ValueError('API key expirada.')
    if not api_key.verificar_secret(secret):
        raise ValueError('Secret invalido.')

    permissoes = [(_texto(item).lower()) for item in (permissoes or []) if _texto(item)]
    for permissao in permissoes:
        if not api_key.possui_permissao(permissao):
            raise PermissionError('Permissao insuficiente para esta integracao.')

    _aplicar_rate_limit(api_key)
    api_key.registrar_uso()
    api_key_repository.salvar()
    return api_key


def _aplicar_rate_limit(api_key: ApiKey):
    agora = datetime.now().timestamp()
    janela = _RATE_LIMIT_BUCKETS[api_key.id]
    while janela and (agora - janela[0]) >= 60:
        janela.popleft()
    limite = max(1, int(api_key.rate_limit or 100))
    if len(janela) >= limite:
        raise RuntimeError('Rate limit excedido para esta API key.')
    janela.append(agora)
