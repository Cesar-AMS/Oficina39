from __future__ import annotations

from datetime import datetime, timedelta
import warnings

from extensions import db
from models import Saida
from services.caixa_service import (
    obter_conferencia_formas,
    obter_fluxo_serializado,
    obter_saldo_atual,
    registrar_saida,
)


def _normalizar_valor_positivo(valor):
    valor_numerico = float(valor)
    if valor_numerico <= 0:
        raise ValueError('Valor deve ser maior que zero')
    return valor_numerico


def _categoria_caixa_para_saida(categoria_legado):
    categoria = (categoria_legado or '').strip().lower()
    return 'retirada' if categoria == 'retirada' else 'despesa'


def _parse_data_recebida(data_str):
    return datetime.strptime(data_str, '%Y-%m-%d') if data_str else datetime.now()


def periodo_por_data(data_str=None):
    if data_str:
        base = datetime.strptime(data_str, '%Y-%m-%d')
    else:
        base = datetime.now()
    inicio = base.replace(hour=0, minute=0, second=0, microsecond=0)
    fim = base.replace(hour=23, minute=59, second=59, microsecond=999999)
    return inicio, fim


def resolver_intervalo_periodo(periodo):
    hoje = datetime.now()
    if periodo == 'dia':
        data_inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
        data_fim = hoje.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif periodo == 'semana':
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        data_inicio = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
        data_fim = data_inicio + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
    elif periodo == 'mes':
        data_inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if hoje.month == 12:
            prox_mes = hoje.replace(year=hoje.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            prox_mes = hoje.replace(month=hoje.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        data_fim = prox_mes - timedelta(microseconds=1)
    else:
        raise ValueError('Período inválido')
    return data_inicio, data_fim


def obter_fluxo_periodo(periodo):
    warnings.warn(
        'fluxo_service.obter_fluxo_periodo está depreciado. Use caixa_service como fonte única.',
        DeprecationWarning,
        stacklevel=2,
    )
    data_inicio, data_fim = resolver_intervalo_periodo(periodo)
    return obter_fluxo_serializado(data_inicio, data_fim)


def obter_saldo(data_corte=None):
    warnings.warn(
        'fluxo_service.obter_saldo está depreciado. Use caixa_service.obter_saldo_atual().',
        DeprecationWarning,
        stacklevel=2,
    )
    return obter_saldo_atual(data_corte)


def criar_saida(dados):
    if not dados.get('descricao') or not dados.get('valor'):
        raise ValueError('Descrição e valor são obrigatórios')

    data_obj = _parse_data_recebida(dados.get('data'))
    valor = _normalizar_valor_positivo(dados['valor'])

    saida = Saida(
        descricao=dados['descricao'],
        valor=valor,
        data=data_obj,
        categoria=dados.get('categoria', 'Outros')
    )
    db.session.add(saida)
    db.session.flush()
    registrar_saida(
        valor=valor,
        categoria=_categoria_caixa_para_saida(saida.categoria),
        descricao=saida.descricao,
        data_movimento=saida.data,
        commit=False,
    )
    db.session.commit()
    return saida


def fechamento_conferencia(dados):
    warnings.warn(
        'fluxo_service.fechamento_conferencia está depreciado. Use caixa_service para leituras de conferência.',
        DeprecationWarning,
        stacklevel=2,
    )
    data_ref = (dados.get('data') or '').strip()
    contagem = dados.get('contagem') or {}
    if not isinstance(contagem, dict):
        raise TypeError('contagem deve ser um objeto.')

    data_inicio, data_fim = periodo_por_data(data_ref)
    resultado = obter_conferencia_formas(data_inicio, data_fim, contagem)
    resultado['data'] = data_inicio.strftime('%Y-%m-%d')
    return resultado
