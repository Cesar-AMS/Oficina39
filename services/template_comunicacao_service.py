from __future__ import annotations

import re

from models import TemplateComunicacao
from repositories import template_comunicacao_repository
from services.comunicacao_service import criar_comunicacao


TEMPLATES_PADRAO = [
    {
        'nome': 'os_criada',
        'canal': 'email',
        'assunto': 'OS #{{ordem.id}} criada com sucesso',
        'corpo': 'Olá {{cliente.nome}}, sua ordem de serviço #{{ordem.id}} foi criada com status "{{ordem.status}}". Total previsto: R$ {{ordem.total_geral}}.',
        'ativo': True,
    },
    {
        'nome': 'os_concluida',
        'canal': 'whatsapp',
        'assunto': None,
        'corpo': 'Olá {{cliente.nome}}, sua OS #{{ordem.id}} foi concluída. Valor total: R$ {{ordem.total_cobrado}}. Forma de pagamento: {{ordem.forma_pagamento}}.',
        'ativo': True,
    },
    {
        'nome': 'os_paga',
        'canal': 'email',
        'assunto': 'Pagamento confirmado da OS #{{ordem.id}}',
        'corpo': 'Olá {{cliente.nome}}, confirmamos o pagamento da OS #{{ordem.id}}. Status financeiro: {{ordem.status_financeiro}}. Obrigado pela preferência.',
        'ativo': True,
    },
]


def _texto(valor):
    return (valor or '').strip()


def listar_templates(filtros: dict | None = None):
    filtros = filtros or {}
    ativo = filtros.get('ativo')
    if isinstance(ativo, str):
        ativo = ativo.strip().lower() in {'1', 'true', 'sim', 'yes'}
    return template_comunicacao_repository.listar(
        nome=filtros.get('nome'),
        canal=filtros.get('canal'),
        ativo=ativo if filtros.get('ativo') is not None else None,
    )


def obter_template(template_id: int) -> TemplateComunicacao:
    template = template_comunicacao_repository.buscar_por_id(template_id)
    if not template:
        raise LookupError('Template de comunicacao nao encontrado.')
    return template


def criar_template(dados: dict) -> TemplateComunicacao:
    nome = _texto((dados or {}).get('nome'))
    canal = _texto((dados or {}).get('canal')).lower()
    corpo = _texto((dados or {}).get('corpo'))
    assunto = _texto((dados or {}).get('assunto')) or None
    ativo = bool((dados or {}).get('ativo', True))

    if not nome:
        raise ValueError('Nome do template e obrigatorio.')
    if not canal:
        raise ValueError('Canal do template e obrigatorio.')
    if not corpo:
        raise ValueError('Corpo do template e obrigatorio.')
    if template_comunicacao_repository.buscar_por_nome(nome):
        raise ValueError('Ja existe template com este nome.')

    template = TemplateComunicacao(
        nome=nome,
        canal=canal,
        assunto=assunto,
        corpo=corpo,
        ativo=ativo,
    )
    template_comunicacao_repository.criar(template)
    template_comunicacao_repository.salvar()
    return template


def atualizar_template(template_id: int, dados: dict) -> TemplateComunicacao:
    template = obter_template(template_id)
    dados = dados or {}

    if 'nome' in dados:
        nome = _texto(dados.get('nome'))
        if not nome:
            raise ValueError('Nome do template e obrigatorio.')
        existente = template_comunicacao_repository.buscar_por_nome(nome)
        if existente and existente.id != template.id:
            raise ValueError('Ja existe template com este nome.')
        template.nome = nome
    if 'canal' in dados:
        template.canal = _texto(dados.get('canal')).lower()
    if 'assunto' in dados:
        template.assunto = _texto(dados.get('assunto')) or None
    if 'corpo' in dados:
        corpo = _texto(dados.get('corpo'))
        if not corpo:
            raise ValueError('Corpo do template e obrigatorio.')
        template.corpo = corpo
    if 'ativo' in dados:
        template.ativo = bool(dados.get('ativo'))

    template_comunicacao_repository.salvar()
    return template


def garantir_templates_padrao():
    for item in TEMPLATES_PADRAO:
        existente = template_comunicacao_repository.buscar_por_nome(item['nome'])
        if existente:
            continue
        template_comunicacao_repository.criar(TemplateComunicacao(**item))
    template_comunicacao_repository.salvar()


def _resolver_placeholder(contexto: dict, caminho: str):
    atual = contexto
    for parte in (caminho or '').split('.'):
        if isinstance(atual, dict):
            atual = atual.get(parte)
        else:
            atual = None
        if atual is None:
            return ''
    return str(atual)


def _renderizar(texto: str | None, contexto: dict) -> str | None:
    if texto is None:
        return None
    return re.sub(r'{{\s*([a-zA-Z0-9_.]+)\s*}}', lambda m: _resolver_placeholder(contexto, m.group(1)), texto)


def _destino_por_canal(canal: str, contexto: dict) -> str | None:
    cliente = contexto.get('cliente') or {}
    if canal == 'email':
        return _texto(cliente.get('email'))
    if canal in {'whatsapp', 'sms'}:
        return _texto(cliente.get('telefone'))
    return None


def montar_contexto_ordem(ordem) -> dict:
    cliente = ordem.cliente
    return {
        'ordem': {
            'id': ordem.id,
            'status': ordem.status,
            'forma_pagamento': ordem.forma_pagamento or '',
            'total_geral': f'{float(ordem.total_geral or 0):.2f}',
            'total_cobrado': f'{float(ordem.total_cobrado or 0):.2f}',
            'total_pago': f'{float(ordem.total_pago or 0):.2f}',
            'saldo_pendente': f'{float(ordem.saldo_pendente or 0):.2f}',
            'status_financeiro': ordem.status_financeiro,
        },
        'cliente': {
            'id': cliente.id if cliente else None,
            'nome': getattr(cliente, 'nome_cliente', '') if cliente else '',
            'email': getattr(cliente, 'email', '') if cliente else '',
            'telefone': getattr(cliente, 'telefone', '') if cliente else '',
        },
    }


def disparar_template(nome_template: str, contexto: dict, entidade_tipo=None, entidade_id=None, processar_agora: bool = False):
    template = template_comunicacao_repository.buscar_por_nome(nome_template)
    if not template or not template.ativo:
        return None

    destino = _destino_por_canal(template.canal, contexto)
    if not destino:
        return None

    return criar_comunicacao({
        'canal': template.canal,
        'destino': destino,
        'assunto': _renderizar(template.assunto, contexto),
        'mensagem': _renderizar(template.corpo, contexto),
        'entidade_tipo': entidade_tipo,
        'entidade_id': entidade_id,
        'metadata': {
            'template_nome': template.nome,
        },
    }, processar_agora=processar_agora)


def disparar_evento_ordem(nome_template: str, ordem, processar_agora: bool = False):
    return disparar_template(
        nome_template=nome_template,
        contexto=montar_contexto_ordem(ordem),
        entidade_tipo='ordem',
        entidade_id=ordem.id,
        processar_agora=processar_agora,
    )
