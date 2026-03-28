# ===========================================
# routes/paginas_routes.py - Rotas das Paginas HTML
# ===========================================

from flask import Blueprint, render_template

paginas_bp = Blueprint('paginas', __name__)


@paginas_bp.route('/')
def index():
    """Pagina inicial com menu principal"""
    return render_template('index.html')


@paginas_bp.route('/cadastroCliente.html')
def cadastro_cliente_page():
    """Pagina de cadastro de cliente"""
    return render_template('cadastroCliente.html')


@paginas_bp.route('/consultarOS.html')
def consultar_os_page():
    """Pagina de consulta de ordens de servico"""
    return render_template('consultarOS.html')


@paginas_bp.route('/visualizarOS.html')
def visualizar_os_page():
    """Pagina de visualizacao de ordem de servico"""
    return render_template('visualizarOS.html')


@paginas_bp.route('/preview-orcamento.html')
def preview_orcamento_page():
    """Pagina de pre-visualizacao do orcamento em PDF"""
    return render_template('previewOrcamento.html')


@paginas_bp.route('/editarOS.html')
def editar_os_page():
    """Pagina de edicao de ordem de servico"""
    return render_template('editarOS.html')


@paginas_bp.route('/nova-os')
def nova_os_page():
    """Pagina de criacao de nova ordem de servico"""
    return render_template('novaOS.html')


@paginas_bp.route('/fluxo_caixa.html')
def fluxo_caixa_page():
    """Pagina de fluxo de caixa"""
    return render_template('fluxoCaixa.html')


@paginas_bp.route('/debitos.html')
def debitos_page():
    """Pagina de debitos em aberto"""
    return render_template('debitos.html')


@paginas_bp.route('/config_contador.html')
def config_contador_page():
    """Pagina de configuracoes do contador"""
    return render_template('config.html')


@paginas_bp.route('/relatorios/producao-profissionais')
def relatorio_producao_profissionais_page():
    """Pagina de producao/faturamento por profissional"""
    return render_template('producaoProfissionais.html')
