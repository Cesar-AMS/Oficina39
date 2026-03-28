from __future__ import annotations

from desktop.infrastructure.execution_context import DesktopExecutionContext
from desktop.repositories.order_repository import get_order_by_id
from desktop.services.order_view_service import load_order_view
from services.ordem_service import atualizar_ordem as atualizar_ordem_service


def load_order_edit(order_id: int) -> dict:
    return load_order_view(order_id)


def save_order_edit(order_id: int, payload: dict) -> dict:
    order = get_order_by_id(order_id)
    if not order:
        raise LookupError("Ordem não encontrada.")

    context = DesktopExecutionContext()
    atualizar_ordem_service(order, payload, context)
    return load_order_view(order_id)
