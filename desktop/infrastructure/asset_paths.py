from __future__ import annotations

import os


def project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def resolve_public_path(path: str | None) -> str | None:
    if not path:
        return None

    normalized = path.strip().replace("/", os.sep).lstrip("\\/")
    if not normalized:
        return None

    base_dir = project_root()
    candidate = os.path.join(base_dir, normalized)
    if os.path.exists(candidate):
        return candidate

    return None


def default_logo_path() -> str | None:
    base_dir = project_root()
    candidates = [
        os.path.join(base_dir, "imagemlogopicapau.png"),
        os.path.join(base_dir, "icone.ico"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None
