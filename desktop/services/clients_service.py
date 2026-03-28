from __future__ import annotations

from services.cliente_service import (
    create_client,
    delete_client,
    get_client,
    list_clients,
    lookup_cep,
    lookup_plate,
    search_clients,
    update_client,
)


def _to_dict(client) -> dict:
    return client.to_dict() if client else {}


def list_all_clients() -> list[dict]:
    return [_to_dict(client) for client in list_clients()]


def find_clients(term: str) -> list[dict]:
    term = (term or "").strip()
    clients = search_clients(term) if term else list_clients()
    return [_to_dict(client) for client in clients]


def load_client(client_id: int) -> dict:
    client = get_client(client_id)
    if not client:
        raise LookupError("Cliente nao encontrado.")
    return _to_dict(client)


def save_client(payload: dict, client_id: int | None = None) -> dict:
    if client_id is None:
        client = create_client(payload)
    else:
        client = update_client(client_id, payload)
    return _to_dict(client)


def remove_client(client_id: int) -> None:
    delete_client(client_id)


def fetch_address_by_cep(cep: str) -> dict:
    return lookup_cep(cep)


def fetch_vehicle_by_plate(plate: str) -> dict:
    return lookup_plate(plate)
