# ===========================================
# routes/paginas_routes.py - Rotas das Páginas HTML
# ===========================================

from flask import Blueprint, render_template

# Criar o blueprint (não precisa de prefixo)
paginas_bp = Blueprint('paginas', __name__)

# ===========================================
# PÁGINA INICIAL
# ===========================================
@paginas_bp.route('/')
def index():
    """Página inicial com menu principal"""
    return render_template('index.html')

# ===========================================
# CADASTRO DE CLIENTE
# ===========================================
@paginas_bp.route('/cadastroCliente.html')
def cadastro_cliente_page():
    """Página de cadastro de cliente"""
    return render_template('cadastroCliente.html')

# ===========================================
# CONSULTA DE ORDENS
# ===========================================
@paginas_bp.route('/consultarOS.html')
def consultar_os_page():
    """Página de consulta de ordens de serviço"""
    return render_template('consultarOS.html')

# ===========================================
# VISUALIZAR ORDEM
# ===========================================
@paginas_bp.route('/visualizarOS.html')
def visualizar_os_page():
    """Página de visualização de ordem de serviço"""
    return render_template('visualizarOS.html')

# ===========================================
# EDITAR ORDEM
# ===========================================
@paginas_bp.route('/editarOS.html')
def editar_os_page():
    """Página de edição de ordem de serviço"""
    return render_template('editarOS.html')

# ===========================================
# NOVA ORDEM
# ===========================================
@paginas_bp.route('/nova-os')
def nova_os_page():
    """Página de criação de nova ordem de serviço"""
    return render_template('novaOS.html')

# ===========================================
# FLUXO DE CAIXA
# ===========================================
@paginas_bp.route('/fluxo_caixa.html')
def fluxo_caixa_page():
    """Página de fluxo de caixa"""
    return render_template('fluxoCaixa.html')

# ===========================================
# CONFIGURAÇÕES
# ===========================================
@paginas_bp.route('/config_contador.html')
def config_contador_page():
    """Página de configurações do contador"""
    return render_template('config.html')

# ===========================================
# RELATÓRIO - PRODUÇÃO POR PROFISSIONAL
# ===========================================
@paginas_bp.route('/relatorios/producao-profissionais')
def relatorio_producao_profissionais_page():
    """Página de produção/faturamento por profissional"""
    return render_template('producaoProfissionais.html')
