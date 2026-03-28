from __future__ import annotations

from datetime import datetime

from repositories import cliente_repository as legacy_cliente_repository
from repositories import ordem_repository as legacy_ordem_repository
from repositories import profissional_repository as legacy_profissional_repository


def list_all_orders():
    return legacy_ordem_repository.listar_todas()


def search_orders(*, cliente: str = "", status: str = "", profissional: str = ""):
    return legacy_ordem_repository.buscar_por_filtros(
        cliente=cliente,
        status=status,
        profissional=profissional,
    )


def get_order_by_id(order_id: int):
    return legacy_ordem_repository.buscar_por_id(order_id)


def get_client_by_id(client_id: int):
    return legacy_cliente_repository.buscar_por_id(client_id)


def list_active_professionals():
    return legacy_profissional_repository.listar(ativos_apenas=True)
