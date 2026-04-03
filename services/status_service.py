from models import StatusLog
from repositories.status_log_repository import status_log_repository


ENTIDADES_COM_STATUS = {'ordem', 'cliente', 'pagamento'}


def _contexto_operacional(request_ctx):
    operador = 'sistema'
    origem = 'api'
    usuario_id = None

    if request_ctx is not None:
        headers = getattr(request_ctx, 'headers', None)
        args = getattr(request_ctx, 'args', None)
        if headers is not None:
            operador = (headers.get('X-Operador') or operador).strip()[:80] or 'sistema'
            origem = (headers.get('X-Origem') or origem).strip()[:40] or 'api'
            usuario_bruto = headers.get('X-Usuario-Id')
            if usuario_bruto is not None:
                try:
                    usuario_id = int(usuario_bruto)
                except (TypeError, ValueError):
                    usuario_id = None
        if args is not None:
            operador = (args.get('operador') or operador).strip()[:80] or operador

    return operador, origem, usuario_id


def registrar_transicao_status(
    entidade_tipo,
    entidade_id,
    status_anterior,
    status_novo,
    motivo=None,
    metadata=None,
    request_ctx=None,
):
    entidade = (entidade_tipo or '').strip().lower()
    if entidade not in ENTIDADES_COM_STATUS:
        raise ValueError('Tipo de entidade invalido para historico de status.')
    if not entidade_id:
        raise ValueError('Entidade de historico nao informada.')
    if not (status_novo or '').strip():
        raise ValueError('Status novo nao informado.')

    operador, origem, usuario_id = _contexto_operacional(request_ctx)

    log = StatusLog(
        entidade_tipo=entidade,
        entidade_id=int(entidade_id),
        status_anterior=(status_anterior or '').strip() or None,
        status_novo=(status_novo or '').strip(),
        motivo=(motivo or '').strip()[:200] or None,
        usuario_id=usuario_id,
        metadata_json=dict(metadata or {}),
        operador=operador,
        origem=origem,
    )
    return status_log_repository.criar(log)


def registrar_status_ordem(
    ordem,
    request_ctx,
    status_anterior,
    status_novo,
    forma_pagamento=None,
    observacao=None,
):
    metadata = {}
    if forma_pagamento:
        metadata['forma_pagamento'] = forma_pagamento
    if observacao:
        metadata['observacao'] = observacao

    return registrar_transicao_status(
        entidade_tipo='ordem',
        entidade_id=ordem.id,
        status_anterior=status_anterior,
        status_novo=status_novo,
        motivo=observacao,
        metadata=metadata,
        request_ctx=request_ctx,
    )


def listar_historico_status(entidade_tipo, entidade_id):
    return status_log_repository.listar_por_entidade(entidade_tipo, entidade_id, incluir_legado=True)
