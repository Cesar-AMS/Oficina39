# ===========================================
# controllers/__init__.py - Centralizador de Controllers
# ===========================================

from .clientes_routes import clientes_bp
from .ordens_routes import ordens_bp
from .servicos_routes import servicos_bp
from .pecas_routes import pecas_bp
from .fluxo_routes import fluxo_bp
from .profissionais_routes import profissionais_bp
from .config_routes import config_bp
from .debitos_routes import debitos_bp
from .export_routes import export_bp
from .relatorios_routes import relatorios_bp
from .paginas_routes import paginas_bp
from .integracoes_routes import integracoes_bp

import logging

# Lista de todos os blueprints para registrar no app.py
blueprints = [
    clientes_bp,
    ordens_bp,
    servicos_bp,
    pecas_bp,
    fluxo_bp,
    profissionais_bp,
    config_bp,
    debitos_bp,
    export_bp,
    relatorios_bp,
    paginas_bp,
    integracoes_bp
]

logger = logging.getLogger(__name__)
logger.debug(f"Blueprints carregados: {len(blueprints)}")
for bp in blueprints:
    logger.debug(f"   - {bp.name}")
