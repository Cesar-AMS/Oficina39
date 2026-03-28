"""Bootstrap transicional do desktop.

No curto prazo, esta camada inicializa o contexto legado para permitir
reaproveitamento dos models/services/repositories atuais sem renderizar
telas via Flask. A interface nativa PyQt5 passa a ser a unica camada de UI.
"""

from __future__ import annotations

from typing import Any


_legacy_app: Any | None = None
_legacy_context: Any | None = None


def bootstrap_legacy_context() -> Any:
    global _legacy_app, _legacy_context

    if _legacy_context is not None:
        return _legacy_context

    from app import create_app

    _legacy_app = create_app(start_scheduler=False)
    _legacy_context = _legacy_app.app_context()
    _legacy_context.push()
    return _legacy_context
