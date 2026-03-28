from sqlalchemy import func

from models import Saida
from extensions import db


def listar_todas():
    return Saida.query.order_by(Saida.data.desc()).all()


def buscar_por_id(saida_id):
    return db.session.get(Saida, saida_id)


def listar_por_periodo(data_inicio, data_fim):
    return (
        Saida.query
        .filter(Saida.data >= data_inicio, Saida.data <= data_fim)
        .order_by(Saida.data.desc())
        .all()
    )


def somar_por_periodo(data_inicio, data_fim):
    row = (
        Saida.query
        .with_entities(func.coalesce(func.sum(Saida.valor), 0.0))
        .filter(Saida.data >= data_inicio, Saida.data <= data_fim)
        .first()
    )
    return float((row[0] if row else 0) or 0)
