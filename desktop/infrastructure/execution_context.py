from __future__ import annotations


class DesktopExecutionContext:
    """Contexto neutro para reutilizar services legados fora do Flask."""

    def __init__(self, operador: str = "desktop", origem: str = "desktop") -> None:
        self.headers = {
            "X-Operador": operador,
            "X-Origem": origem,
        }
        self.args = {}
