from __future__ import annotations

from datetime import datetime
from math import ceil
import re

from flask import current_app
from flask_mail import Message

from extensions import mail
from models import CANAIS_COMUNICACAO, STATUS_COMUNICACAO, Comunicacao
from repositories import comunicacao_repository
from services.validacao_service import ValidacaoService


def _texto(valor) -> str:
    return (valor or '').strip()


def _normalizar_canal(canal: str) -> str:
    valor = _texto(canal).lower()
    if valor not in CANAIS_COMUNICACAO:
        raise ValueError('Canal de comunicacao invalido.')
    return valor


def _normalizar_status(status: str) -> str:
    valor = _texto(status).lower()
    if valor and valor not in STATUS_COMUNICACAO:
        raise ValueError('Status de comunicacao invalido.')
    return valor


def _normalizar_destino(canal: str, destino: str) -> str:
    destino_limpo = _texto(destino)
    if not destino_limpo:
        raise ValueError('Destino da comunicacao e obrigatorio.')
    if canal == 'email':
        if not ValidacaoService.validar_email(destino_limpo):
            raise ValueError('Destino de e-mail invalido.')
        return destino_limpo.lower()

    numeros = re.sub(r'\D', '', destino_limpo)
    if len(numeros) < 10:
        raise ValueError('Destino telefonico invalido.')
    return numeros


def _criar_registro(payload: dict) -> Comunicacao:
    canal = _normalizar_canal(payload.get('canal'))
    comunicacao = Comunicacao(
        canal=canal,
        destino=_normalizar_destino(canal, payload.get('destino')),
        assunto=_texto(payload.get('assunto')) or None,
        mensagem=_texto(payload.get('mensagem')),
        status=_normalizar_status(payload.get('status') or 'pendente') or 'pendente',
        erro=_texto(payload.get('erro')) or None,
        entidade_tipo=_texto(payload.get('entidade_tipo')).lower() or None,
        entidade_id=int(payload.get('entidade_id')) if payload.get('entidade_id') not in (None, '') else None,
    )
    if not comunicacao.mensagem:
        raise ValueError('Mensagem da comunicacao e obrigatoria.')
    comunicacao.metadata_extra = payload.get('metadata') or {}
    return comunicacao


def criar_comunicacao(dados: dict, processar_agora: bool = False) -> Comunicacao:
    comunicacao = _criar_registro(dados or {})
    comunicacao_repository.criar(comunicacao)
    comunicacao_repository.salvar()
    if processar_agora:
        return processar_comunicacao(comunicacao.id)
    return comunicacao


def listar_comunicacoes(filtros: dict | None = None, pagina: int = 1, limite: int = 20) -> dict:
    filtros = filtros or {}
    pagina = max(1, int(pagina or 1))
    limite = max(1, min(100, int(limite or 20)))

    itens, total = comunicacao_repository.listar(
        canal=filtros.get('canal'),
        status=filtros.get('status'),
        entidade_tipo=filtros.get('entidade_tipo'),
        entidade_id=filtros.get('entidade_id'),
        pagina=pagina,
        limite=limite,
    )
    return {
        'itens': [item.to_dict() for item in itens],
        'pagina': pagina,
        'limite': limite,
        'total': total,
        'total_paginas': max(1, ceil(total / limite)) if total else 1,
    }


def obter_comunicacao(comunicacao_id: int) -> Comunicacao:
    comunicacao = comunicacao_repository.obter_por_id(comunicacao_id)
    if not comunicacao:
        raise LookupError('Comunicacao nao encontrada.')
    return comunicacao


def _enviar_email(comunicacao: Comunicacao):
    metadata = comunicacao.metadata_extra
    remetente = _texto(metadata.get('remetente') or current_app.config.get('MAIL_USERNAME'))
    senha = _texto(metadata.get('senha') or current_app.config.get('MAIL_PASSWORD'))
    if not remetente or not senha:
        raise RuntimeError('Credenciais SMTP nao configuradas para envio de e-mail.')

    mail.username = remetente
    mail.password = senha
    mail.sender = remetente
    mail.extract_config()

    msg = Message(
        subject=comunicacao.assunto or 'Mensagem do sistema',
        sender=remetente,
        recipients=[comunicacao.destino],
    )
    if metadata.get('html'):
        msg.html = comunicacao.mensagem
    else:
        msg.body = comunicacao.mensagem

    with mail.connect() as conn:
        conn.send(msg)


def _enviar_whatsapp(comunicacao: Comunicacao):
    raise RuntimeError('Canal WhatsApp ainda nao configurado neste ambiente.')


def _enviar_sms(comunicacao: Comunicacao):
    raise RuntimeError('Canal SMS ainda nao configurado neste ambiente.')


def processar_comunicacao(comunicacao_id: int) -> Comunicacao:
    comunicacao = obter_comunicacao(comunicacao_id)
    try:
        if comunicacao.canal == 'email':
            _enviar_email(comunicacao)
        elif comunicacao.canal == 'whatsapp':
            _enviar_whatsapp(comunicacao)
        elif comunicacao.canal == 'sms':
            _enviar_sms(comunicacao)
        else:
            raise RuntimeError('Canal de comunicacao nao suportado.')

        comunicacao.status = 'enviado'
        comunicacao.erro = None
        comunicacao.enviado_em = datetime.now()
    except Exception as exc:
        comunicacao.status = 'falhou'
        comunicacao.erro = str(exc)[:500]
        comunicacao.enviado_em = None
    comunicacao_repository.salvar()
    return comunicacao


def processar_pendentes(limite: int = 20):
    itens = comunicacao_repository.listar_pendentes(limite=limite)
    return [processar_comunicacao(item.id) for item in itens]


def enviar_email_imediato(destino: str, assunto: str, mensagem: str, entidade_tipo=None, entidade_id=None, remetente=None, senha=None, html=True):
    return criar_comunicacao({
        'canal': 'email',
        'destino': destino,
        'assunto': assunto,
        'mensagem': mensagem,
        'entidade_tipo': entidade_tipo,
        'entidade_id': entidade_id,
        'metadata': {
            'remetente': remetente,
            'senha': senha,
            'html': bool(html),
        },
    }, processar_agora=True)
