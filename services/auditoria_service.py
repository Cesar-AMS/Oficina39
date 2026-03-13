from extensions import db


def registrar_evento_auditoria(
    acao,
    entidade,
    entidade_id=None,
    valor_anterior=None,
    valor_novo=None,
    observacao=None,
    request_ctx=None
):
    """
    Registra auditoria operacional sem interromper o fluxo principal em caso de erro.
    """
    try:
        from models import AuditoriaEvento

        operador = 'sistema'
        origem = 'api'
        if request_ctx is not None:
            operador = (
                request_ctx.headers.get('X-Operador')
                or request_ctx.args.get('operador')
                or 'sistema'
            ).strip()[:80]
            origem = (request_ctx.headers.get('X-Origem') or 'api').strip()[:40]

        evento = AuditoriaEvento(
            acao=(acao or '').strip()[:80] or 'ACAO_NAO_INFORMADA',
            entidade=(entidade or '').strip()[:80] or 'ENTIDADE_NAO_INFORMADA',
            entidade_id=entidade_id,
            valor_anterior=(str(valor_anterior)[:120] if valor_anterior is not None else None),
            valor_novo=(str(valor_novo)[:120] if valor_novo is not None else None),
            observacao=(str(observacao)[:255] if observacao is not None else None),
            operador=operador or 'sistema',
            origem=origem or 'api'
        )
        db.session.add(evento)
    except Exception:
        # Não derruba operação principal por falha de auditoria.
        pass
