from __future__ import annotations

from repositories import cliente_repository as legacy_cliente_repository


def get_client_by_id(client_id: int):
    return legacy_cliente_repository.buscar_por_id(client_id)


def search_clients(term: str, limit: int = 20):
    return legacy_cliente_repository.buscar_por_termo(term, limite=limit)
