from __future__ import annotations

from datetime import datetime

from desktop.infrastructure.execution_context import DesktopExecutionContext
from desktop.models.order_summary import DailyOrderSummary, OrderSummary
from desktop.repositories.order_repository import (
    get_client_by_id,
    get_order_by_id,
    list_active_professionals,
    search_orders,
)
from services.ordem_service import atualizar_ordem as atualizar_ordem_service


STATUS_ALIAS_MAP = {
    "todas": "",
    "aguardando": "Aguardando",
    "andamento": "Em andamento",
    "concluido": "Concluído",
    "garantia": "Garantia",
}


def _parse_pt_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%d/%m/%Y %H:%M")
    except ValueError:
        return None


def _vehicle_label(order_dict: dict) -> str:
    cliente = order_dict.get("cliente") or {}
    fabricante = (cliente.get("fabricante") or "").strip()
    modelo = (cliente.get("modelo") or "").strip()
    vehicle = " ".join(part for part in [fabricante, modelo] if part).strip()
    return vehicle or "---"


def _to_summary(order) -> OrderSummary:
    order_dict = order.to_dict()
    cliente = get_client_by_id(order.cliente_id)
    if cliente:
        order_dict["cliente"] = cliente.to_dict()
    return OrderSummary(
        id=order.id,
        cliente_id=order.cliente_id,
        cliente_nome=order_dict.get("cliente_nome") or (order_dict.get("cliente") or {}).get("nome_cliente") or "---",
        veiculo=_vehicle_label(order_dict),
        placa=((order_dict.get("cliente") or {}).get("placa") or "---"),
        profissional=(order.profissional_responsavel or "").strip() or "---",
        valor_total=float(order.total_geral or 0),
        status=order.status or "---",
        data_entrada=order_dict.get("data_entrada") or "",
    )


def list_orders(cliente_term: str = "", status_alias: str = "todas") -> list[OrderSummary]:
    status = STATUS_ALIAS_MAP.get(status_alias, "")
    if status_alias == "aguardando":
        raw_orders = search_orders(cliente=cliente_term)
        filtered_orders = [o for o in raw_orders if o.status in {"Aguardando", "Aguardando peças"}]
        return [_to_summary(order) for order in filtered_orders]

    raw_orders = search_orders(cliente=cliente_term, status=status) if (cliente_term or status) else search_orders()
    return [_to_summary(order) for order in raw_orders]


def build_daily_summary(orders: list[OrderSummary]) -> DailyOrderSummary:
    today = datetime.now().date()
    orders_today = []
    for order in orders:
        dt = _parse_pt_datetime(order.data_entrada)
        if dt and dt.date() == today:
            orders_today.append(order)

    abertas = sum(1 for order in orders_today if order.status in {"Aguardando", "Aguardando peças"})
    em_execucao = sum(1 for order in orders_today if order.status == "Em andamento")
    concluidas = sum(1 for order in orders_today if order.status in {"Concluído", "Garantia"})
    sem_profissional = sum(1 for order in orders_today if order.profissional == "---")

    return DailyOrderSummary(
        abertas=abertas,
        em_execucao=em_execucao,
        concluidas=concluidas,
        total_dia=len(orders_today),
        sem_profissional=sem_profissional,
    )


def get_order_details(order_id: int) -> dict:
    order = get_order_by_id(order_id)
    if not order:
        raise LookupError("Ordem não encontrada.")

    payload = order.to_dict()
    client = get_client_by_id(order.cliente_id)
    payload["cliente"] = client.to_dict() if client else {}
    return payload


def get_professional_names() -> list[str]:
    return [professional.nome for professional in list_active_professionals() if (professional.nome or "").strip()]


def update_order_professional(order_id: int, professional_name: str) -> None:
    order = get_order_by_id(order_id)
    if not order:
        raise LookupError("Ordem não encontrada.")

    context = DesktopExecutionContext()
    atualizar_ordem_service(
        order,
        {
            "profissional_responsavel": professional_name,
            "forcar_edicao": True,
        },
        context,
    )
