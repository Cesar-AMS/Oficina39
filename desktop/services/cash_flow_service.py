from __future__ import annotations

from datetime import date

from services.fluxo_service import (
    criar_saida as create_output_entry,
    fechamento_conferencia as build_cash_conference,
    obter_fluxo_periodo,
)


def load_daily_cash_flow() -> dict:
    return obter_fluxo_periodo("dia")


def summarize_cash_flow(data: dict) -> dict:
    entradas = data.get("entradas") or []
    saidas = data.get("saidas") or []
    total_entradas = float(sum(float(item.get("total") or 0) for item in entradas))
    total_saidas = float(sum(float(item.get("valor") or 0) for item in saidas))
    return {
        "total_entradas": total_entradas,
        "total_saidas": total_saidas,
        "saldo": total_entradas - total_saidas,
    }


def build_movements(data: dict) -> list[dict]:
    entradas = [
        {
            "horario": item.get("hora") or "--:--",
            "tipo": "Entrada",
            "origem": item.get("origem") or "Recebimento",
            "forma": item.get("forma_pagamento") or "---",
            "valor": float(item.get("total") or 0),
            "observacao": item.get("observacao") or item.get("cliente_nome") or "Sem observação",
            "data_hora_iso": item.get("data_hora_iso") or "",
            "id": item.get("id"),
        }
        for item in (data.get("entradas") or [])
    ]
    saidas = [
        {
            "horario": item.get("hora") or "--:--",
            "tipo": "Saída",
            "origem": item.get("origem") or "Saída manual",
            "forma": item.get("forma_pagamento") or "---",
            "valor": float(item.get("valor") or 0),
            "observacao": item.get("observacao") or item.get("descricao") or "Sem observação",
            "data_hora_iso": item.get("data_hora_iso") or "",
            "id": item.get("id"),
        }
        for item in (data.get("saidas") or [])
    ]
    return sorted([*entradas, *saidas], key=lambda item: str(item.get("data_hora_iso") or ""), reverse=True)


def register_output(descricao: str, valor: float, data_ref: date, categoria: str) -> dict:
    output = create_output_entry(
        {
            "descricao": descricao,
            "valor": valor,
            "data": data_ref.isoformat(),
            "categoria": categoria or "Outros",
        }
    )
    return output.to_dict()


def get_cash_conference(data_ref: date, counted_values: dict[str, float]) -> dict:
    return build_cash_conference(
        {
            "data": data_ref.isoformat(),
            "contagem": counted_values,
        }
    )
