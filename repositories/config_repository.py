from models import AuditoriaEvento, ConfigContador, EnvioRelatorio


def obter_config_contador():
    return ConfigContador.query.first()


def listar_envios(limite=20):
    return EnvioRelatorio.query.order_by(EnvioRelatorio.data_envio.desc()).limit(limite).all()


def listar_auditoria_eventos(limite=50):
    return (
        AuditoriaEvento.query
        .order_by(AuditoriaEvento.data_evento.desc())
        .limit(limite)
        .all()
    )
