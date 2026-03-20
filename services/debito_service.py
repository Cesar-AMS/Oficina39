from datetime import datetime

from extensions import db
from models import OrdemPagamento
from repositories import debito_repository, ordem_repository
from services.auditoria_service import registrar_evento_auditoria
from services.ordem_service import STATUS_CONCLUIDOS, normalizar_forma_pagamento, registrar_log_status


FORMAS_PAGAMENTO_MULTIPLAS = {
    'Dinheiro', 'Pix', 'Cartão', 'Cartão débito', 'Cartão crédito',
    'Transferência', 'Boleto', 'Outro'
}


def listar_debitos_abertos():
    return debito_repository.listar_debitos_abertos()


def _validar_e_anexar_pagamentos(ordem, pagamentos):
    if not isinstance(pagamentos, list) or not pagamentos:
        raise ValueError('Informe pelo menos um pagamento.')

    saldo_antes = float(ordem.saldo_pendente or 0)
    if saldo_antes <= 0:
        raise ValueError('Esta ordem já está quitada.')

    total_pagamento = 0.0
    formas_utilizadas = []
    for item in pagamentos:
        valor = float(item.get('valor') or 0)
        forma = normalizar_forma_pagamento(item.get('forma_pagamento'))
        observacao = (item.get('observacao') or '').strip() or None

        if valor <= 0:
            raise ValueError('Os valores de pagamento devem ser maiores que zero.')
        if not forma or forma not in FORMAS_PAGAMENTO_MULTIPLAS:
            raise ValueError('Forma de pagamento inválida.')

        db.session.add(OrdemPagamento(
            ordem_id=ordem.id,
            valor=valor,
            forma_pagamento=forma,
            observacao=observacao
        ))
        total_pagamento += valor
        formas_utilizadas.append(forma)

    if total_pagamento - saldo_antes > 0.009:
        raise ValueError('O total informado ultrapassa o saldo pendente da ordem.')

    db.session.flush()
    return saldo_antes, formas_utilizadas, total_pagamento


def _aplicar_forma_pagamento_ordem(ordem, formas_utilizadas, manter_nao_informado=False):
    formas = list(dict.fromkeys(formas_utilizadas))
    if not formas:
        if manter_nao_informado:
            ordem.forma_pagamento = 'Não informado'
        return
    if len(formas) == 1:
        ordem.forma_pagamento = formas[0]
    else:
        ordem.forma_pagamento = 'Múltiplos'


def registrar_pagamentos(ordem_id, pagamentos, request_ctx):
    ordem = ordem_repository.buscar_por_id(ordem_id)
    if not ordem:
        raise LookupError('Ordem não encontrada.')

    saldo_antes, formas_utilizadas, _ = _validar_e_anexar_pagamentos(ordem, pagamentos)
    _aplicar_forma_pagamento_ordem(ordem, formas_utilizadas)

    saldo_depois = float(ordem.saldo_pendente or 0)

    registrar_evento_auditoria(
        acao='RECEBIMENTO_OS',
        entidade='ordem',
        entidade_id=ordem.id,
        valor_anterior=f'{saldo_antes:.2f}',
        valor_novo=f'{saldo_depois:.2f}',
        observacao=f'Recebimento registrado ({len(pagamentos)} pagamento(s)).',
        request_ctx=request_ctx
    )

    db.session.commit()
    return ordem


def faturar_ordem_no_caixa(ordem_id, dados, request_ctx):
    ordem = ordem_repository.buscar_por_id(ordem_id)
    if not ordem:
        raise LookupError('Ordem não encontrada.')

    status_anterior = ordem.status
    dados = dados or {}
    pagamentos = dados.get('pagamentos') or []
    debito_vencimento = (dados.get('debito_vencimento') or '').strip()
    debito_observacao = (dados.get('debito_observacao') or '').strip() or None
    desconto_percentual = float(dados.get('desconto_percentual') or 0)
    formas_previstas = []
    for item in pagamentos:
        forma = normalizar_forma_pagamento(item.get('forma_pagamento'))
        if forma:
            formas_previstas.append(forma)

    if ordem.status not in STATUS_CONCLUIDOS:
        ordem.status = 'Concluído'
        if not ordem.data_conclusao:
            from datetime import datetime
            ordem.data_conclusao = datetime.now()
        _aplicar_forma_pagamento_ordem(ordem, formas_previstas, manter_nao_informado=True)
        registrar_log_status(
            ordem,
            request_ctx,
            status_anterior=status_anterior,
            status_novo=ordem.status,
            forma_pagamento=ordem.forma_pagamento,
            observacao='Conclusão via PDV / Caixa'
        )

    if desconto_percentual < 0 or desconto_percentual > 100:
        raise ValueError('O desconto percentual deve ficar entre 0 e 100.')

    ordem.desconto_percentual = round(desconto_percentual, 2)
    ordem.desconto_valor = round(float(ordem.total_geral or 0) * (ordem.desconto_percentual / 100), 2)

    if float(ordem.total_cobrado or 0) + 0.0001 < float(ordem.total_pago or 0):
        raise ValueError('O desconto informado deixa o total cobrado menor que o valor já pago desta OS.')

    saldo_antes = float(ordem.saldo_pendente or 0)
    if pagamentos:
        saldo_antes, formas_utilizadas, _ = _validar_e_anexar_pagamentos(ordem, pagamentos)
        _aplicar_forma_pagamento_ordem(ordem, formas_utilizadas, manter_nao_informado=True)
        saldo_depois = float(ordem.saldo_pendente or 0)
        registrar_evento_auditoria(
            acao='RECEBIMENTO_OS',
            entidade='ordem',
            entidade_id=ordem.id,
            valor_anterior=f'{saldo_antes:.2f}',
            valor_novo=f'{saldo_depois:.2f}',
            observacao=f'Recebimento via PDV ({len(pagamentos)} pagamento(s)).',
            request_ctx=request_ctx
        )

    saldo_final = float(ordem.saldo_pendente or 0)
    if saldo_final > 0.009:
        if debito_vencimento:
            try:
                ordem.debito_vencimento = datetime.strptime(debito_vencimento, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError('Data de vencimento do débito inválida. Use YYYY-MM-DD.')
        ordem.debito_observacao = debito_observacao
    else:
        ordem.debito_vencimento = None
        ordem.debito_observacao = None

    db.session.commit()
    return ordem
