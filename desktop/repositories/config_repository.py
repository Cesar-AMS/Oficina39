from __future__ import annotations

from models import ConfigContador
from repositories import config_repository as legacy_config_repository


def get_current_config() -> ConfigContador | None:
    return legacy_config_repository.obter_config_contador()
