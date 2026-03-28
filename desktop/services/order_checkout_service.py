from __future__ import annotations

from desktop.infrastructure.execution_context import DesktopExecutionContext
from desktop.services.order_view_service import load_order_view
from services.debito_service import (
    FORMA_RECEBER_DEPOIS,
    FORMAS_PAGAMENTO_MULTIPLAS,
    faturar_ordem_no_caixa as faturar_ordem_no_caixa_service,
)


def get_checkout_metadata() -> dict:
    formas = sorted(FORMAS_PAGAMENTO_MULTIPLAS)
    formas.append(FORMA_RECEBER_DEPOIS)
    return {"formas_pagamento": formas}


def load_checkout_order(order_id: int) -> dict:
    return load_order_view(order_id)


def finalize_order_in_cashier(order_id: int, payload: dict) -> dict:
    context = DesktopExecutionContext(operador="desktop-caixa", origem="desktop-caixa")
    order = faturar_ordem_no_caixa_service(order_id, payload, context)
    return order.to_dict()
