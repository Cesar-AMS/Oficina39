from __future__ import annotations

from desktop.infrastructure.execution_context import DesktopExecutionContext
from desktop.repositories.client_repository import get_client_by_id, search_clients
from desktop.repositories.order_repository import get_order_by_id, list_active_professionals
from services.ordem_service import criar_ordem as criar_ordem_service


INITIAL_STATUS = "Aguardando"


def _client_to_dict(client) -> dict:
    return client.to_dict() if client else {}


def get_new_order_metadata() -> dict:
    professionals = [item.nome for item in list_active_professionals() if (item.nome or "").strip()]
    return {
        "status_inicial": INITIAL_STATUS,
        "profissionais": professionals,
    }


def find_clients(term: str) -> list[dict]:
    return [_client_to_dict(client) for client in search_clients(term)]


def load_client(client_id: int) -> dict:
    client = get_client_by_id(client_id)
    if not client:
        raise LookupError("Cliente nao encontrado.")
    return _client_to_dict(client)


def create_order(payload: dict) -> dict:
    context = DesktopExecutionContext()
    order = criar_ordem_service(payload, context)
    refreshed = get_order_by_id(order.id)
    if not refreshed:
        raise LookupError("Falha ao carregar a ordem criada.")
    return refreshed.to_dict()
