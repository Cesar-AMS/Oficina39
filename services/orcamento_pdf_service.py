from __future__ import annotations

from services.order_pdf_service import generate_order_preview_pdf_bytes


def gerar_pdf_preview(dados: dict) -> bytes:
    """Gera o PDF do orcamento usando o mesmo layout do PDF oficial da OS."""
    return generate_order_preview_pdf_bytes(dados or {})
