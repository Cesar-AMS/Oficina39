from datetime import datetime
import warnings

from extensions import db
from repositories import cliente_repository, ordem_repository
from services.auditoria_service import registrar_evento_auditoria
from services import peca_service, servico_service
from services.status_service import registrar_status_ordem
from services.template_comunicacao_service import disparar_evento_ordem
from services.webhook_service import disparar_evento_webhook, payload_ordem

STATUS_CONCLUIDOS = {'Concluído', 'Garantia'}
FORMAS_PAGAMENTO_VALIDAS = {
    'Dinheiro', 'Pix', 'Cartão', 'Cartão débito', 'Cartão crédito',
    'Transferência', 'Boleto', 'Outro', 'Múltiplos', 'Não informado'
}


def normalizar_forma_pagamento(valor):
    forma = (valor or '').strip()
    if not forma:
        return None
    mapping = {
        'dinheiro': 'Dinheiro',
        'pix': 'Pix',
        'cartao': 'Cartão',
        'cartão': 'Cartão',
        'cartao debito': 'Cartão débito',
        'cartão débito': 'Cartão débito',
        'cartao credito': 'Cartão crédito',
        'cartão crédito': 'Cartão crédito',
        'boleto': 'Boleto',
        'transferencia': 'Transferência',
        'transferência': 'Transferência',
        'outro': 'Outro',
        'multiplos': 'Múltiplos',
        'múltiplos': 'Múltiplos',
        'nao informado': 'Não informado',
        'não informado': 'Não informado'
    }
    return mapping.get(forma.lower(), forma)


def parse_data_iso(valor):
    if not valor:
        return None
    return datetime.strptime(valor, '%Y-%m-%d')


def registrar_log_status(ordem, request_ctx, status_anterior, status_novo, forma_pagamento=None, observacao=None):
    return registrar_status_ordem(
        ordem=ordem,
        request_ctx=request_ctx,
        status_anterior=status_anterior,
        status_novo=status_novo,
        forma_pagamento=forma_pagamento,
        observacao=observacao,
    )


def _recalcular_totais_manualmente(ordem):
    ordem.total_servicos = servico_service.calcular_total_servicos(ordem.servicos)
    ordem.total_pecas = peca_service.calcular_total_pecas(ordem.pecas)
    ordem.total_geral = ordem.total_servicos + ordem.total_pecas

def criar_ordem(dados, request_ctx):
    from models import Ordem

    cliente_id = dados.get('cliente_id')
    if not cliente_id:
        raise ValueError('Cliente é obrigatório')

    cliente = cliente_repository.buscar_por_id(cliente_id)
    if not cliente:
        raise LookupError('Cliente não encontrado')

    profissional_responsavel = (dados.get('profissional_responsavel') or '').strip()
    if not profissional_responsavel:
        raise ValueError('Profissional responsável é obrigatório.')
    if not ordem_repository.profissional_ativo_existe(profissional_responsavel):
        raise ValueError('Profissional responsável inválido. Selecione um profissional cadastrado e ativo.')

    ordem = Ordem(
        cliente_id=cliente_id,
        diagnostico=dados.get('diagnostico', ''),
        observacao_interna=dados.get('observacao_interna', ''),
        profissional_responsavel=profissional_responsavel,
        assinatura_cliente=dados.get('assinatura_cliente', ''),
        status='Aguardando',
        forma_pagamento=normalizar_forma_pagamento(dados.get('forma_pagamento'))
    )
    db.session.add(ordem)
    db.session.flush()

    servico_service.anexar_servicos_em_ordem(ordem, dados.get('servicos', []))
    peca_service.anexar_pecas_em_ordem(ordem, dados.get('pecas', []))

    db.session.flush()
    _recalcular_totais_manualmente(ordem)
    registrar_log_status(ordem, request_ctx, None, ordem.status, forma_pagamento=ordem.forma_pagamento, observacao='Criação da ordem')
    db.session.commit()
    disparar_evento_ordem('os_criada', ordem)
    disparar_evento_webhook('os.criada', payload_ordem(ordem))
    return ordem


def atualizar_ordem(ordem, dados, request_ctx):
    if ordem.status in STATUS_CONCLUIDOS and not bool(dados.get('forcar_edicao')):
        raise ValueError('Ordem concluída está bloqueada para edição. Reabra a ordem para alterar.')

    total_geral_anterior = float(ordem.total_geral or 0)

    if 'diagnostico' in dados:
        ordem.diagnostico = dados['diagnostico']
    if 'observacao_interna' in dados:
        ordem.observacao_interna = dados['observacao_interna']

    profissional_anterior = (ordem.profissional_responsavel or '').strip()
    if 'profissional_responsavel' in dados:
        novo_profissional = (dados.get('profissional_responsavel') or '').strip()
        if not novo_profissional:
            raise ValueError('Profissional responsável é obrigatório.')
        if not ordem_repository.profissional_ativo_existe(novo_profissional):
            raise ValueError('Profissional responsável inválido. Selecione um profissional cadastrado e ativo.')
        ordem.profissional_responsavel = novo_profissional

    if 'assinatura_cliente' in dados:
        ordem.assinatura_cliente = dados['assinatura_cliente']
    if 'data_retirada' in dados:
        valor_data_retirada = dados.get('data_retirada')
        if valor_data_retirada:
            if isinstance(valor_data_retirada, datetime):
                ordem.data_retirada = valor_data_retirada
            else:
                try:
                    ordem.data_retirada = datetime.strptime(str(valor_data_retirada), '%Y-%m-%d')
                except ValueError:
                    raise ValueError('Data de retirada inválida. Use o formato YYYY-MM-DD.')
        else:
            ordem.data_retirada = None
    if 'status' in dados:
        ordem.status = dados['status']
    if 'forma_pagamento' in dados:
        ordem.forma_pagamento = normalizar_forma_pagamento(dados.get('forma_pagamento'))

    if 'servicos' in dados:
        servico_service.substituir_servicos_da_ordem(ordem, dados['servicos'])
    elif 'profissional_responsavel' in dados:
        servico_service.atualizar_profissional_dos_servicos(ordem)

    if 'pecas' in dados:
        peca_service.substituir_pecas_da_ordem(ordem, dados['pecas'])

    db.session.flush()
    _recalcular_totais_manualmente(ordem)
    total_geral_novo = float(ordem.total_geral or 0)

    if abs(total_geral_novo - total_geral_anterior) > 0.0001:
        registrar_evento_auditoria(
            acao='ALTERACAO_VALOR_OS',
            entidade='ordem',
            entidade_id=ordem.id,
            valor_anterior=f'{total_geral_anterior:.2f}',
            valor_novo=f'{total_geral_novo:.2f}',
            observacao='Valor total da OS alterado por edição.',
            request_ctx=request_ctx
        )

    db.session.commit()
    return profissional_anterior


def atualizar_status(ordem, dados, request_ctx):
    novo_status = dados.get('status')
    if not novo_status:
        raise ValueError('Status não informado')

    status_validos = ['Aguardando', 'Aguardando peças', 'Em andamento', 'Concluído', 'Garantia']
    if novo_status not in status_validos:
        raise ValueError('Status inválido')
    if novo_status in STATUS_CONCLUIDOS and not (ordem.profissional_responsavel or '').strip():
        raise ValueError('Não é possível finalizar sem profissional responsável definido.')
    if novo_status in STATUS_CONCLUIDOS and not ordem_repository.profissional_ativo_existe(ordem.profissional_responsavel):
        raise ValueError('Não é possível finalizar com profissional não cadastrado/ativo.')

    forma_pagamento = normalizar_forma_pagamento(dados.get('forma_pagamento'))
    if forma_pagamento and forma_pagamento not in FORMAS_PAGAMENTO_VALIDAS:
        raise ValueError('Forma de pagamento inválida')

    status_anterior = ordem.status
    ordem.status = novo_status
    if forma_pagamento:
        ordem.forma_pagamento = forma_pagamento

    if novo_status in STATUS_CONCLUIDOS:
        if dados.get('data_conclusao'):
            try:
                data_str = dados['data_conclusao'].replace('Z', '+00:00')
                ordem.data_conclusao = datetime.fromisoformat(data_str)
            except Exception:
                ordem.data_conclusao = datetime.now()
        else:
            ordem.data_conclusao = datetime.now()

    registrar_log_status(
        ordem,
        request_ctx,
        status_anterior=status_anterior,
        status_novo=novo_status,
        forma_pagamento=ordem.forma_pagamento,
        observacao=(dados.get('observacao') or '').strip() or None
    )
    db.session.commit()
    if novo_status in STATUS_CONCLUIDOS:
        disparar_evento_ordem('os_concluida', ordem)
        disparar_evento_webhook('os.concluida', payload_ordem(ordem))
    return status_anterior


def deletar_ordem(ordem, request_ctx):
    registrar_evento_auditoria(
        acao='EXCLUSAO_OS',
        entidade='ordem',
        entidade_id=ordem.id,
        valor_anterior=f'{float(ordem.total_geral or 0):.2f}',
        valor_novo='0.00',
        observacao='OS removida.',
        request_ctx=request_ctx
    )
    db.session.delete(ordem)
    db.session.commit()


def reabrir_ordem(ordem, request_ctx):
    if ordem.status not in STATUS_CONCLUIDOS:
        raise ValueError('Somente ordens concluídas ou em garantia podem ser reabertas.')

    status_anterior = ordem.status
    ordem.status = 'Em andamento'
    registrar_log_status(
        ordem,
        request_ctx,
        status_anterior=status_anterior,
        status_novo='Em andamento',
        forma_pagamento=ordem.forma_pagamento,
        observacao='Reabertura da ordem'
    )
    registrar_evento_auditoria(
        acao='REABERTURA_OS',
        entidade='ordem',
        entidade_id=ordem.id,
        valor_anterior=status_anterior,
        valor_novo='Em andamento',
        observacao='Ordem reaberta para edição.',
        request_ctx=request_ctx
    )
    db.session.commit()


def duplicar_ordem(origem, request_ctx):
    from models import Ordem

    nova = Ordem(
        cliente_id=origem.cliente_id,
        diagnostico=origem.diagnostico or '',
        observacao_interna=origem.observacao_interna or '',
        profissional_responsavel=origem.profissional_responsavel or '',
        assinatura_cliente='',
        status='Aguardando',
        forma_pagamento=None
    )
    db.session.add(nova)
    db.session.flush()

    servico_service.duplicar_servicos_da_ordem(origem, nova)
    peca_service.duplicar_pecas_da_ordem(origem, nova)

    db.session.flush()
    _recalcular_totais_manualmente(nova)
    registrar_log_status(nova, request_ctx, None, nova.status, observacao=f'Duplicada da OS #{origem.id}')
    db.session.commit()
    return nova


def _adicionar_servico_os_impl(ordem_id, servico_id, nome_profissional=None, valor_servico=None):
    ordem = ordem_repository.buscar_por_id(ordem_id)
    if not ordem:
        raise LookupError('Ordem nao encontrada.')
    if ordem.status in STATUS_CONCLUIDOS:
        raise ValueError('Nao e possivel adicionar servico em ordem concluida.')

    servico_service.adicionar_servico_em_ordem(
        ordem=ordem,
        servico_id=servico_id,
        nome_profissional=nome_profissional,
        valor_servico=valor_servico,
    )
    db.session.flush()
    _recalcular_totais_manualmente(ordem)
    db.session.commit()
    return ordem


def adicionar_servico_os(ordem_id, servico_id, nome_profissional=None, valor_servico=None):
    warnings.warn(
        'adicionar_servico_os esta depreciado. Use servico_service diretamente.',
        DeprecationWarning,
        stacklevel=2,
    )
    return _adicionar_servico_os_impl(
        ordem_id=ordem_id,
        servico_id=servico_id,
        nome_profissional=nome_profissional,
        valor_servico=valor_servico,
    )


def _adicionar_peca_os_impl(ordem_id, peca_id, quantidade=1, valor_unitario=None):
    ordem = ordem_repository.buscar_por_id(ordem_id)
    if not ordem:
        raise LookupError('Ordem nao encontrada.')
    if ordem.status in STATUS_CONCLUIDOS:
        raise ValueError('Nao e possivel adicionar peca em ordem concluida.')

    peca_service.adicionar_peca_em_ordem(
        ordem=ordem,
        peca_id=peca_id,
        quantidade=quantidade,
        valor_unitario=valor_unitario,
    )
    db.session.flush()
    _recalcular_totais_manualmente(ordem)
    db.session.commit()
    return ordem


def adicionar_peca_os(ordem_id, peca_id, quantidade=1, valor_unitario=None):
    warnings.warn(
        'adicionar_peca_os esta depreciado. Use peca_service diretamente.',
        DeprecationWarning,
        stacklevel=2,
    )
    return _adicionar_peca_os_impl(
        ordem_id=ordem_id,
        peca_id=peca_id,
        quantidade=quantidade,
        valor_unitario=valor_unitario,
    )
