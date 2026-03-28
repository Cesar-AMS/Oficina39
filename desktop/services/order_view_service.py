from __future__ import annotations

from desktop.repositories.order_repository import get_client_by_id, get_order_by_id
from repositories import ordem_repository as legacy_ordem_repository


def load_order_view(order_id: int) -> dict:
    order = get_order_by_id(order_id)
    if not order:
        raise LookupError("Ordem não encontrada.")

    payload = order.to_dict()
    client = get_client_by_id(order.cliente_id)
    payload["cliente"] = client.to_dict() if client else {}

    logs = legacy_ordem_repository.listar_logs_status(order_id)
    payload["logs_status"] = [log.to_dict() for log in logs]
    return payload
