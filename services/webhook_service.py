from __future__ import annotations

from datetime import datetime
import hashlib
import hmac
import json
import time
from urllib import request as urllib_request

from models import Webhook
from repositories import api_key_repository, webhook_repository
from services.api_key_service import obter_secret_api_key


def _texto(valor) -> str:
    return (valor or '').strip()


def _normalizar_eventos(eventos) -> list[str]:
    if not isinstance(eventos, (list, tuple, set)):
        raise ValueError('Lista de eventos invalida.')
    itens = []
    for item in eventos:
        valor = _texto(item).lower()
        if valor:
            itens.append(valor)
    itens = sorted(set(itens))
    if not itens:
        raise ValueError('Informe ao menos um evento.')
    return itens


def _normalizar_url(url: str) -> str:
    valor = _texto(url)
    if not valor:
        raise ValueError('URL do webhook e obrigatoria.')
    if not (valor.startswith('http://') or valor.startswith('https://')):
        raise ValueError('URL do webhook invalida.')
    return valor


def _normalizar_int(valor, padrao: int, campo: str) -> int:
    try:
        numero = int(valor if valor is not None else padrao)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{campo} invalido.') from exc
    if numero < 1:
        raise ValueError(f'{campo} deve ser maior que zero.')
    return numero


def listar_webhooks(filtros: dict | None = None):
    filtros = filtros or {}
    ativo = filtros.get('ativo')
    if isinstance(ativo, str):
        ativo = ativo.strip().lower() in {'1', 'true', 'sim', 'yes'}
    return webhook_repository.listar(
        ativo=ativo if filtros.get('ativo') is not None else None,
        evento=filtros.get('evento'),
    )


def obter_webhook(webhook_id: int) -> Webhook:
    webhook = webhook_repository.buscar_por_id(webhook_id)
    if not webhook:
        raise LookupError('Webhook nao encontrado.')
    return webhook


def criar_webhook(dados: dict) -> Webhook:
    dados = dados or {}
    api_key_id = dados.get('api_key_id')
    if api_key_id not in (None, ''):
        api_key = api_key_repository.buscar_por_id(int(api_key_id))
        if not api_key:
            raise ValueError('API key associada nao encontrada.')
    webhook = Webhook(
        url=_normalizar_url(dados.get('url')),
        api_key_id=int(api_key_id) if api_key_id not in (None, '') else None,
        ativo=bool(dados.get('ativo', True)),
        tentativas=_normalizar_int(dados.get('tentativas'), 3, 'Tentativas'),
        timeout=_normalizar_int(dados.get('timeout'), 10, 'Timeout'),
    )
    webhook.eventos = _normalizar_eventos(dados.get('eventos') or [])
    webhook_repository.criar(webhook)
    webhook_repository.salvar()
    return webhook


def atualizar_webhook(webhook_id: int, dados: dict) -> Webhook:
    webhook = obter_webhook(webhook_id)
    dados = dados or {}
    if 'url' in dados:
        webhook.url = _normalizar_url(dados.get('url'))
    if 'eventos' in dados:
        webhook.eventos = _normalizar_eventos(dados.get('eventos') or [])
    if 'api_key_id' in dados:
        api_key_id = dados.get('api_key_id')
        if api_key_id in (None, ''):
            webhook.api_key_id = None
        else:
            api_key = api_key_repository.buscar_por_id(int(api_key_id))
            if not api_key:
                raise ValueError('API key associada nao encontrada.')
            webhook.api_key_id = int(api_key_id)
    if 'ativo' in dados:
        webhook.ativo = bool(dados.get('ativo'))
    if 'tentativas' in dados:
        webhook.tentativas = _normalizar_int(dados.get('tentativas'), 3, 'Tentativas')
    if 'timeout' in dados:
        webhook.timeout = _normalizar_int(dados.get('timeout'), 10, 'Timeout')
    webhook_repository.salvar()
    return webhook


def desativar_webhook(webhook_id: int) -> Webhook:
    webhook = obter_webhook(webhook_id)
    webhook.ativo = False
    webhook_repository.salvar()
    return webhook


def _headers_webhook(webhook: Webhook) -> dict:
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Oficina39-Webhook/1.0',
    }
    if webhook.api_key:
        headers['X-Webhook-Key'] = webhook.api_key.key
    return headers


def _gerar_assinatura(payload: dict, secret: str) -> str:
    mensagem = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hmac.new(
        (secret or '').encode('utf-8'),
        mensagem.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


def disparar_webhook(webhook: Webhook, evento: str, payload: dict) -> dict:
    ultimo_erro = None
    status_code = None
    for _ in range(max(1, int(webhook.tentativas or 1))):
        try:
            timestamp = str(int(time.time()))
            envelope = {
                'evento': evento,
                'payload': payload,
                'webhook_id': webhook.id,
                'timestamp': timestamp,
            }
            headers = _headers_webhook(webhook)
            headers['X-Webhook-Event'] = evento
            headers['X-Webhook-Timestamp'] = timestamp
            if webhook.api_key_id:
                secret = obter_secret_api_key(webhook.api_key_id)
                headers['X-Webhook-Signature'] = _gerar_assinatura(envelope, secret)
            corpo = json.dumps(envelope, ensure_ascii=False).encode('utf-8')
            req = urllib_request.Request(
                webhook.url,
                data=corpo,
                headers=headers,
                method='POST',
            )
            with urllib_request.urlopen(req, timeout=max(1, int(webhook.timeout or 10))) as response:
                status_code = int(getattr(response, 'status', response.getcode()))
            webhook.ultima_chamada = datetime.now()
            webhook.ultimo_status = status_code
            webhook_repository.salvar()
            if 200 <= status_code < 300:
                return {'ok': True, 'status': status_code}
            ultimo_erro = f'HTTP {status_code}'
        except Exception as exc:
            ultimo_erro = str(exc)

    webhook.ultima_chamada = datetime.now()
    webhook.ultimo_status = status_code
    webhook_repository.salvar()
    return {'ok': False, 'status': status_code, 'erro': ultimo_erro}


def disparar_evento_webhook(evento: str, payload: dict):
    resultados = []
    for webhook in webhook_repository.listar(ativo=True, evento=evento):
        resultados.append({
            'webhook_id': webhook.id,
            **disparar_webhook(webhook, evento, payload),
        })
    return resultados


def payload_ordem(ordem) -> dict:
    cliente = ordem.cliente
    return {
        'ordem': {
            'id': ordem.id,
            'status': ordem.status,
            'status_financeiro': ordem.status_financeiro,
            'total_geral': float(ordem.total_geral or 0),
            'total_cobrado': float(ordem.total_cobrado or 0),
            'total_pago': float(ordem.total_pago or 0),
            'saldo_pendente': float(ordem.saldo_pendente or 0),
            'forma_pagamento': ordem.forma_pagamento,
            'profissional_responsavel': ordem.profissional_responsavel,
        },
        'cliente': {
            'id': cliente.id if cliente else None,
            'nome': getattr(cliente, 'nome_cliente', '') if cliente else '',
            'email': getattr(cliente, 'email', '') if cliente else '',
            'telefone': getattr(cliente, 'telefone', '') if cliente else '',
        },
    }


def payload_cliente(cliente) -> dict:
    return {
        'cliente': {
            'id': cliente.id,
            'nome': cliente.nome_cliente,
            'cpf': cliente.cpf,
            'email': cliente.email,
            'telefone': cliente.telefone,
            'cidade': cliente.cidade,
            'estado': cliente.estado,
        }
    }
