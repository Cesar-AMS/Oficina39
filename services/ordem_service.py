from datetime import datetime

from extensions import db
from repositories import cliente_repository, ordem_repository
from services.auditoria_service import registrar_evento_auditoria

STATUS_CONCLUIDOS = {'Concluído', 'Garantia'}
FORMAS_PAGAMENTO_VALIDAS = {'Dinheiro', 'Pix', 'Cartão', 'Boleto', 'Transferência', 'Não informado'}


def normalizar_forma_pagamento(valor):
    forma = (valor or '').strip()
    if not forma:
        return None
    mapping = {
        'dinheiro': 'Dinheiro',
        'pix': 'Pix',
        'cartao': 'Cartão',
        'cartão': 'Cartão',
        'boleto': 'Boleto',
        'transferencia': 'Transferência',
        'transferência': 'Transferência',
        'nao informado': 'Não informado',
        'não informado': 'Não informado'
    }
    return mapping.get(forma.lower(), forma)


def parse_data_iso(valor):
    if not valor:
        return None
    return datetime.strptime(valor, '%Y-%m-%d')


def registrar_log_status(ordem, request_ctx, status_anterior, status_novo, forma_pagamento=None, observacao=None):
    from models import OrdemStatusLog

    operador = (request_ctx.headers.get('X-Operador') or request_ctx.args.get('operador') or 'sistema').strip()[:80]
    origem = (request_ctx.headers.get('X-Origem') or 'api').strip()[:40]

    log = OrdemStatusLog(
        ordem_id=ordem.id,
        status_anterior=status_anterior,
        status_novo=status_novo,
        forma_pagamento=forma_pagamento,
        operador=operador or 'sistema',
        origem=origem or 'api',
        observacao=(observacao or '').strip()[:255] or None
    )
    db.session.add(log)


def _recalcular_totais_manualmente(ordem):
    ordem.total_servicos = sum(float(s.valor_servico or 0) for s in ordem.servicos)
    ordem.total_pecas = sum(float((p.quantidade or 0) * (p.valor_unitario or 0)) for p in ordem.pecas)
    ordem.total_geral = ordem.total_servicos + ordem.total_pecas


def criar_ordem(dados, request_ctx):
    from models import ItemPeca, ItemServico, Ordem

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

    for servico in dados.get('servicos', []):
        if servico.get('descricao_servico'):
            db.session.add(ItemServico(
                ordem_id=ordem.id,
                codigo_servico=servico.get('codigo_servico', ''),
                descricao_servico=servico['descricao_servico'],
                nome_profissional=(servico.get('nome_profissional') or ordem.profissional_responsavel or '').strip(),
                valor_servico=servico.get('valor_servico', 0)
            ))

    for peca in dados.get('pecas', []):
        if peca.get('descricao_peca'):
            db.session.add(ItemPeca(
                ordem_id=ordem.id,
                codigo_peca=peca.get('codigo_peca', ''),
                descricao_peca=peca['descricao_peca'],
                quantidade=peca.get('quantidade', 1),
                valor_unitario=peca.get('valor_unitario', 0)
            ))

    db.session.flush()
    _recalcular_totais_manualmente(ordem)
    registrar_log_status(ordem, request_ctx, None, ordem.status, forma_pagamento=ordem.forma_pagamento, observacao='Criação da ordem')
    db.session.commit()
    return ordem


def atualizar_ordem(ordem, dados, request_ctx):
    from models import ItemPeca, ItemServico

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
    if 'status' in dados:
        ordem.status = dados['status']
    if 'forma_pagamento' in dados:
        ordem.forma_pagamento = normalizar_forma_pagamento(dados.get('forma_pagamento'))

    if 'servicos' in dados:
        ItemServico.query.filter_by(ordem_id=ordem.id).delete()
        for servico in dados['servicos']:
            if servico.get('descricao_servico'):
                db.session.add(ItemServico(
                    ordem_id=ordem.id,
                    codigo_servico=servico.get('codigo_servico', ''),
                    descricao_servico=servico['descricao_servico'],
                    nome_profissional=(servico.get('nome_profissional') or ordem.profissional_responsavel or '').strip(),
                    valor_servico=servico.get('valor_servico', 0)
                ))
    elif 'profissional_responsavel' in dados:
        ItemServico.query.filter_by(ordem_id=ordem.id).update({'nome_profissional': ordem.profissional_responsavel})

    if 'pecas' in dados:
        ItemPeca.query.filter_by(ordem_id=ordem.id).delete()
        for peca in dados['pecas']:
            if peca.get('descricao_peca'):
                db.session.add(ItemPeca(
                    ordem_id=ordem.id,
                    codigo_peca=peca.get('codigo_peca', ''),
                    descricao_peca=peca['descricao_peca'],
                    quantidade=peca.get('quantidade', 1),
                    valor_unitario=peca.get('valor_unitario', 0)
                ))

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
    from models import ItemPeca, ItemServico, Ordem

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

    for s in origem.servicos:
        db.session.add(ItemServico(
            ordem_id=nova.id,
            codigo_servico=s.codigo_servico,
            descricao_servico=s.descricao_servico,
            nome_profissional=s.nome_profissional or nova.profissional_responsavel or '',
            valor_servico=s.valor_servico or 0
        ))

    for p in origem.pecas:
        db.session.add(ItemPeca(
            ordem_id=nova.id,
            codigo_peca=p.codigo_peca,
            descricao_peca=p.descricao_peca,
            quantidade=p.quantidade or 0,
            valor_unitario=p.valor_unitario or 0
        ))

    db.session.flush()
    _recalcular_totais_manualmente(nova)
    registrar_log_status(nova, request_ctx, None, nova.status, observacao=f'Duplicada da OS #{origem.id}')
    db.session.commit()
    return nova
