from models import AuditoriaEvento
from services.status_service import listar_historico_status


TIPO_STATUS = 'status_log'
TIPO_AUDITORIA = 'auditoria'


def obter_historico_unificado(entidade_tipo=None, entidade_id=None, limite=100):
    entidade = (entidade_tipo or '').strip().lower() or None
    entidade_id_int = _coagir_entidade_id(entidade_id)
    limite_int = _normalizar_limite(limite)

    itens = []

    if entidade and entidade_id_int is not None:
        for log in listar_historico_status(entidade, entidade_id_int):
            itens.append(_serializar_status(log))

    query = AuditoriaEvento.query
    if entidade:
        query = query.filter(AuditoriaEvento.entidade == entidade)
    if entidade_id_int is not None:
        query = query.filter(AuditoriaEvento.entidade_id == entidade_id_int)

    eventos = (
        query.order_by(AuditoriaEvento.data_evento.desc())
        .limit(limite_int)
        .all()
    )
    for evento in eventos:
        itens.append(_serializar_auditoria(evento))

    itens.sort(key=lambda item: item.get('data_ordem') or '', reverse=True)
    return itens[:limite_int]


def _coagir_entidade_id(entidade_id):
    if entidade_id in (None, ''):
        return None
    try:
        return int(entidade_id)
    except (TypeError, ValueError):
        raise ValueError('entidade_id invalido')


def _normalizar_limite(limite):
    try:
        return max(1, min(500, int(limite or 100)))
    except (TypeError, ValueError):
        return 100


def _serializar_status(log):
    dados = log.to_dict()
    data_ref = getattr(log, 'created_at', None) or getattr(log, 'data_evento', None)
    return {
        'tipo': TIPO_STATUS,
        'entidade_tipo': dados.get('entidade_tipo') or 'ordem',
        'entidade_id': dados.get('entidade_id') or dados.get('ordem_id'),
        'acao': 'STATUS_ALTERADO',
        'titulo': f"{dados.get('status_anterior') or '---'} -> {dados.get('status_novo')}",
        'descricao': dados.get('observacao') or dados.get('motivo') or 'Mudanca de status',
        'status_anterior': dados.get('status_anterior'),
        'status_novo': dados.get('status_novo'),
        'operador': dados.get('operador'),
        'origem': dados.get('origem'),
        'data_evento': dados.get('data_evento'),
        'data_ordem': data_ref.isoformat() if data_ref else '',
        'metadata': dados.get('metadata') or {},
        'dados': dados,
    }


def _serializar_auditoria(evento):
    dados = evento.to_dict()
    return {
        'tipo': TIPO_AUDITORIA,
        'entidade_tipo': dados.get('entidade_tipo') or dados.get('entidade'),
        'entidade_id': dados.get('entidade_id'),
        'acao': dados.get('acao'),
        'titulo': dados.get('acao'),
        'descricao': dados.get('observacao') or 'Evento de auditoria',
        'status_anterior': None,
        'status_novo': None,
        'operador': dados.get('operador'),
        'origem': dados.get('origem'),
        'data_evento': dados.get('data_evento'),
        'data_ordem': getattr(evento, 'data_evento', None).isoformat() if getattr(evento, 'data_evento', None) else '',
        'metadata': {
            'valor_anterior': dados.get('valor_anterior'),
            'valor_novo': dados.get('valor_novo'),
        },
        'dados': dados,
    }
