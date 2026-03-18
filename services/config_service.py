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

    config.email_cliente = dados.get('email_cliente', '')
    if dados.get('senha_app'):
        config.senha_app = dados.get('senha_app', '')
    config.email_contador = dados.get('email_contador', '')
    config.profissional_envio_auto = (dados.get('profissional_envio_auto') or '').strip() or None
    config.frequencia = dados.get('frequencia', 'diario')
    config.dia_envio = dados.get('dia_envio', 1)
    config.ativo = dados.get('ativo', True)
    config.cep_provider_ativo = (dados.get('cep_provider_ativo') or '').strip() or None
    config.cep_provider_primario = (dados.get('cep_provider_primario') or '').strip() or None
    config.cep_api_key_primaria = (dados.get('cep_api_key_primaria') or '').strip() or None
    config.cep_provider_secundario = (dados.get('cep_provider_secundario') or '').strip() or None
    config.cep_api_key_secundaria = (dados.get('cep_api_key_secundaria') or '').strip() or None
    config.placa_provider_ativo = (dados.get('placa_provider_ativo') or '').strip() or None
    config.placa_provider_primario = (dados.get('placa_provider_primario') or '').strip() or None
    config.placa_api_key_primaria = (dados.get('placa_api_key_primaria') or '').strip() or None
    config.placa_provider_secundario = (dados.get('placa_provider_secundario') or '').strip() or None
    config.placa_api_key_secundaria = (dados.get('placa_api_key_secundaria') or '').strip() or None

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
