from __future__ import annotations

from functools import wraps

from flask import g, jsonify, request

from services.api_key_service import validar_api_key
from services.usuario_service import validar_token


def _extrair_token():
    header = (request.headers.get('Authorization') or '').strip()
    if header.lower().startswith('bearer '):
        return header[7:].strip()
    return (request.headers.get('X-Auth-Token') or '').strip()


def _extrair_api_key():
    header = (request.headers.get('Authorization') or '').strip()
    if header.lower().startswith('apikey '):
        payload = header[7:].strip()
        if ':' in payload:
            return payload.split(':', 1)[0].strip()
        return payload.strip()
    return (request.headers.get('X-API-Key') or '').strip()


def _extrair_api_secret():
    header = (request.headers.get('Authorization') or '').strip()
    if header.lower().startswith('apikey '):
        payload = header[7:].strip()
        if ':' in payload:
            return payload.split(':', 1)[1].strip()
    return (request.headers.get('X-API-Secret') or '').strip()


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            usuario = validar_token(_extrair_token())
            g.current_user = usuario
            return fn(*args, **kwargs)
        except ValueError as exc:
            return jsonify({'erro': str(exc)}), 401
    return wrapper


def require_profiles(*perfis):
    perfis_validos = {perfil.strip().lower() for perfil in perfis if perfil}

    def decorator(fn):
        @wraps(fn)
        @require_auth
        def wrapper(*args, **kwargs):
            usuario = getattr(g, 'current_user', None)
            if not usuario or usuario.perfil not in perfis_validos:
                return jsonify({'erro': 'Acesso negado.'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_api_key(*permissoes):
    permissoes_validas = tuple((item or '').strip().lower() for item in permissoes if (item or '').strip())

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                api_key = validar_api_key(
                    _extrair_api_key(),
                    _extrair_api_secret(),
                    permissoes=permissoes_validas,
                )
                g.current_api_key = api_key
                g.auth_mode = 'api_key'
                return fn(*args, **kwargs)
            except PermissionError as exc:
                return jsonify({'erro': str(exc)}), 403
            except RuntimeError as exc:
                return jsonify({'erro': str(exc)}), 429
            except ValueError as exc:
                return jsonify({'erro': str(exc)}), 401
        return wrapper
    return decorator


def require_auth_or_api_key(*permissoes):
    permissoes_validas = tuple((item or '').strip().lower() for item in permissoes if (item or '').strip())

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = _extrair_token()
            if token:
                try:
                    usuario = validar_token(token)
                    g.current_user = usuario
                    g.auth_mode = 'user'
                    return fn(*args, **kwargs)
                except ValueError:
                    pass
            try:
                api_key = validar_api_key(
                    _extrair_api_key(),
                    _extrair_api_secret(),
                    permissoes=permissoes_validas,
                )
                g.current_api_key = api_key
                g.auth_mode = 'api_key'
                return fn(*args, **kwargs)
            except PermissionError as exc:
                return jsonify({'erro': str(exc)}), 403
            except RuntimeError as exc:
                return jsonify({'erro': str(exc)}), 429
            except ValueError:
                return jsonify({'erro': 'Autenticacao obrigatoria.'}), 401
        return wrapper
    return decorator
