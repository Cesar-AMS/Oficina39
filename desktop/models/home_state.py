from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class HomeState:
    title: str
    logo_path: str | None
    logo_shape: str
    logo_scale: float
    logo_offset_x: float
    logo_offset_y: float
    company_name: str | None
    company_email: str | None
    company_phone: str | None
    company_address: str | None
