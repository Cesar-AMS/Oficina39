from __future__ import annotations

from dataclasses import dataclass

from services.debito_service import listar_debitos_abertos


@dataclass(slots=True)
class DebtsSummary:
    total_ordens: int
    total_em_aberto: int
    total_parcial: int
    saldo_total: float


def _normalize(value) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("á", "a")
        .replace("à", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )


def _digits(value) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _to_payload(order) -> dict:
    payload = order.to_dict()
    payload["cliente"] = order.cliente.to_dict() if order.cliente else {}
    return payload


def list_open_debts(search_term: str = "") -> list[dict]:
    items = [_to_payload(order) for order in listar_debitos_abertos()]
    term = _normalize(search_term)
    digits = _digits(search_term)
    if not term and not digits:
        return items

    filtered = []
    for item in items:
        client = item.get("cliente") or {}
        name = _normalize(item.get("cliente_nome") or client.get("nome_cliente"))
        cpf = _digits(client.get("cpf"))
        plate = _normalize(client.get("placa"))
        if term in name or term in plate or (digits and digits in cpf):
            filtered.append(item)
    return filtered


def build_debts_summary(items: list[dict]) -> DebtsSummary:
    total_open = sum(1 for item in items if (item.get("status_financeiro") or "") == "Em aberto")
    total_partial = sum(1 for item in items if (item.get("status_financeiro") or "") == "Parcial")
    total_balance = sum(float(item.get("saldo_pendente") or 0) for item in items)
    return DebtsSummary(
        total_ordens=len(items),
        total_em_aberto=total_open,
        total_parcial=total_partial,
        saldo_total=round(total_balance, 2),
    )
