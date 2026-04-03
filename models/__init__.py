# ===========================================
# models/__init__.py - Centralizador de Models
# ===========================================

from .cliente import Cliente
from .cliente_draft import ClienteDraft
from .ordem import Ordem
from .servico import ItemServico, Servico
from .peca import ItemPeca, Peca
from .saida import Saida
from .caixa import (
    CATEGORIAS_MOVIMENTO_CAIXA,
    FORMAS_MOVIMENTO_CAIXA,
    MovimentoCaixa,
    TIPOS_MOVIMENTO_CAIXA,
)
from .config import ConfigContador
from .envio import EnvioRelatorio
from .profissional import Profissional
from .ordem_status_log import OrdemStatusLog
from .ordem_anexo import OrdemAnexo
from .auditoria_evento import AuditoriaEvento
from .ordem_pagamento import OrdemPagamento

# Lista de todos os models para facilitar importação
__all__ = [
    'Cliente',
    'Ordem',
    'Servico',
    'ItemServico',
    'Peca',
    'ItemPeca',
    'Saida',
    'TIPOS_MOVIMENTO_CAIXA',
    'CATEGORIAS_MOVIMENTO_CAIXA',
    'FORMAS_MOVIMENTO_CAIXA',
    'MovimentoCaixa',
    'ConfigContador',
    'EnvioRelatorio',
    'Profissional',
    'OrdemStatusLog',
    'OrdemAnexo',
    'AuditoriaEvento',
    'OrdemPagamento'
    ,'ClienteDraft'
]

import logging
logger = logging.getLogger(__name__)
logger.debug("Models carregados: %s", ', '.join(__all__))
