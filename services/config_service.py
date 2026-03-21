from datetime import datetime, timedelta

from extensions import db
from models import ConfigContador
from repositories import config_repository
from services.relatorio_service import buscar_dados_periodo, gerar_relatorio_html
from infrastructure.email_service import enviar_relatorio_email


def obter_config_contador():
    return config_repository.obter_config_contador()


def salvar_config_contador(dados):
    config = config_repository.obter_config_contador()
    if not config:
        config = ConfigContador()

    def valor_texto(chave, atual=''):
        if chave not in dados:
            return atual
        return dados.get(chave, '')

    def valor_opcional(chave, atual=None):
        if chave not in dados:
            return atual
        return (dados.get(chave) or '').strip() or None

    config.email_cliente = valor_texto('email_cliente', config.email_cliente or '')
    if 'senha_app' in dados and dados.get('senha_app'):
        config.senha_app = dados.get('senha_app', '')
    config.email_contador = valor_texto('email_contador', config.email_contador or '')
    config.profissional_envio_auto = valor_opcional('profissional_envio_auto', config.profissional_envio_auto)
    if 'frequencia' in dados:
        config.frequencia = dados.get('frequencia', 'diario')
    elif not config.frequencia:
        config.frequencia = 'diario'
    if 'dia_envio' in dados:
        config.dia_envio = dados.get('dia_envio', 1)
    elif config.dia_envio is None:
        config.dia_envio = 1
    if 'ativo' in dados:
        config.ativo = dados.get('ativo', True)
    elif config.ativo is None:
        config.ativo = True
    config.cep_provider_ativo = valor_opcional('cep_provider_ativo', config.cep_provider_ativo)
    config.cep_provider_primario = valor_opcional('cep_provider_primario', config.cep_provider_primario)
    config.cep_api_key_primaria = valor_opcional('cep_api_key_primaria', config.cep_api_key_primaria)
    config.cep_provider_secundario = valor_opcional('cep_provider_secundario', config.cep_provider_secundario)
    config.cep_api_key_secundaria = valor_opcional('cep_api_key_secundaria', config.cep_api_key_secundaria)
    config.placa_provider_ativo = valor_opcional('placa_provider_ativo', config.placa_provider_ativo)
    config.placa_provider_primario = valor_opcional('placa_provider_primario', config.placa_provider_primario)
    config.placa_api_key_primaria = valor_opcional('placa_api_key_primaria', config.placa_api_key_primaria)
    config.placa_provider_secundario = valor_opcional('placa_provider_secundario', config.placa_provider_secundario)
    config.placa_api_key_secundaria = valor_opcional('placa_api_key_secundaria', config.placa_api_key_secundaria)
    config.whatsapp_orcamento = valor_opcional('whatsapp_orcamento', config.whatsapp_orcamento)
    config.nome_exibicao_sistema = valor_opcional('nome_exibicao_sistema', config.nome_exibicao_sistema)
    config.empresa_nome = valor_opcional('empresa_nome', config.empresa_nome)
    config.empresa_email = valor_opcional('empresa_email', config.empresa_email)
    config.empresa_telefone = valor_opcional('empresa_telefone', config.empresa_telefone)
    config.empresa_endereco = valor_opcional('empresa_endereco', config.empresa_endereco)
    config.logo_index_path = valor_opcional('logo_index_path', config.logo_index_path)
    config.qrcode_1_path = valor_opcional('qrcode_1_path', config.qrcode_1_path)
    config.qrcode_2_path = valor_opcional('qrcode_2_path', config.qrcode_2_path)
    if 'logo_index_formato' in dados:
        config.logo_index_formato = (dados.get('logo_index_formato') or 'circulo').strip() or 'circulo'
    elif not config.logo_index_formato:
        config.logo_index_formato = 'circulo'

    if not config.id:
        db.session.add(config)

    db.session.commit()
    return config


def _data_inicio_periodo(periodo):
    hoje = datetime.now()
    if periodo == 'diario':
        return hoje.replace(hour=0, minute=0, second=0, microsecond=0), hoje.strftime('%d/%m/%Y')
    if periodo == 'semanal':
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        return inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0), f"Semana de {inicio_semana.strftime('%d/%m')}"
    data_inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return data_inicio, hoje.strftime('%m/%Y')


def enviar_relatorio_teste(dados):
    periodo = dados.get('periodo', 'diario')
    formato = dados.get('formato', 'html')
    email_cliente = dados.get('email_cliente')
    senha_app = dados.get('senha_app')
    email_contador = dados.get('email_contador')

    if not email_cliente or not senha_app or not email_contador:
        raise ValueError('E-mails e senha são obrigatórios')

    data_inicio, nome_periodo = _data_inicio_periodo(periodo)
    entradas, saidas, total_entradas, total_saidas, saldo = buscar_dados_periodo(data_inicio)
    html = gerar_relatorio_html(
        periodo=nome_periodo,
        entradas=entradas,
        saidas=saidas,
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        saldo=saldo
    )

    return enviar_relatorio_email(
        email_cliente,
        senha_app,
        email_contador,
        nome_periodo,
        html,
        formato
    )
