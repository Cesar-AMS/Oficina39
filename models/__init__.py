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
from .status_log import StatusLog
from .anexo import Anexo
from .ordem_anexo import OrdemAnexo
from .auditoria_evento import AuditoriaEvento
from .ordem_pagamento import OrdemPagamento
from .comunicacao import CANAIS_COMUNICACAO, STATUS_COMUNICACAO, Comunicacao
from .template_comunicacao import TemplateComunicacao
from .api_key import ApiKey
from .webhook import Webhook
from .usuario import PERFIS_USUARIO, Usuario

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
    'StatusLog',
    'Anexo',
    'OrdemAnexo',
    'AuditoriaEvento',
    'OrdemPagamento',
    'Comunicacao',
    'CANAIS_COMUNICACAO',
    'STATUS_COMUNICACAO',
    'TemplateComunicacao',
    'ApiKey',
    'Webhook',
    'Usuario',
    'PERFIS_USUARIO'
    ,'ClienteDraft'
]

import logging
logger = logging.getLogger(__name__)
logger.debug("Models carregados: %s", ', '.join(__all__))
