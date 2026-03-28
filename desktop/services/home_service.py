from __future__ import annotations

from desktop.infrastructure.asset_paths import default_logo_path, resolve_public_path
from desktop.models.home_state import HomeState
from desktop.repositories.config_repository import get_current_config


DEFAULT_TITLE = "SISTEMA DE GERENCIAMENTO OFICINA 39"


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def load_home_state() -> HomeState:
    config = get_current_config()

    if not config:
        return HomeState(
            title=DEFAULT_TITLE,
            logo_path=default_logo_path(),
            logo_shape="circulo",
            logo_scale=1.0,
            logo_offset_x=0.0,
            logo_offset_y=0.0,
            company_name=None,
            company_email=None,
            company_phone=None,
            company_address=None,
        )

    title = (
        (config.nome_exibicao_sistema or "").strip()
        or (config.empresa_nome or "").strip()
        or DEFAULT_TITLE
    )

    logo_path = resolve_public_path(config.logo_index_path) or default_logo_path()
    logo_shape = (config.logo_index_formato or "circulo").strip() or "circulo"

    return HomeState(
        title=title,
        logo_path=logo_path,
        logo_shape=logo_shape if logo_shape in {"circulo", "quadrado"} else "circulo",
        logo_scale=_clamp(float(config.logo_index_escala or 1.0), 0.7, 3.0),
        logo_offset_x=_clamp(float(config.logo_index_offset_x or 0.0), -30.0, 30.0),
        logo_offset_y=_clamp(float(config.logo_index_offset_y or 0.0), -30.0, 30.0),
        company_name=(config.empresa_nome or "").strip() or None,
        company_email=(config.empresa_email or "").strip() or None,
        company_phone=(config.empresa_telefone or "").strip() or None,
        company_address=(config.empresa_endereco or "").strip() or None,
    )
