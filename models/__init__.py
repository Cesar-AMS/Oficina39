# ===========================================
# models/__init__.py - Centralizador de Models
# ===========================================

from .cliente import Cliente
from .ordem import Ordem
from .servico import ItemServico
from .peca import ItemPeca
from .saida import Saida
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
    'ItemServico',
    'ItemPeca',
    'Saida',
    'ConfigContador',
    'EnvioRelatorio',
    'Profissional',
    'OrdemStatusLog',
    'OrdemAnexo',
    'AuditoriaEvento',
    'OrdemPagamento'
]

# Opcional: print para debug
print("Models carregados:", ', '.join(__all__))
