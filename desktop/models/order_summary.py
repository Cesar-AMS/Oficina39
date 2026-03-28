from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class OrderSummary:
    id: int
    cliente_id: int
    cliente_nome: str
    veiculo: str
    placa: str
    profissional: str
    valor_total: float
    status: str
    data_entrada: str


@dataclass(slots=True)
class DailyOrderSummary:
    abertas: int
    em_execucao: int
    concluidas: int
    total_dia: int
    sem_profissional: int
