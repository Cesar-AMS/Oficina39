from sqlalchemy.orm import joinedload

from models import Ordem


STATUS_COM_DEBITO = {'Concluído', 'Garantia'}


def listar_debitos_abertos():
    ordens = (
        Ordem.query
        .options(
            joinedload(Ordem.cliente),
            joinedload(Ordem.pagamentos)
        )
        .filter(Ordem.status.in_(STATUS_COM_DEBITO))
        .order_by(Ordem.data_conclusao.desc().nullslast(), Ordem.id.desc())
        .all()
    )
    return [ordem for ordem in ordens if float(ordem.saldo_pendente or 0) > 0.009]
