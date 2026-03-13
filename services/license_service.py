import base64
import hashlib
import hmac
import json
import os
import platform
import subprocess
from datetime import datetime


LICENSE_FILE_DEFAULT = ".oficina39_license.json"
MASTER_KEY_DEFAULT = "OF39-CHANGE-THIS-KEY"


def _safe_text(value):
    return (value or "").strip()


def get_machine_fingerprint():
    parts = [
        platform.system(),
        platform.node(),
        platform.machine(),
        platform.processor(),
    ]

    try:
        output = subprocess.check_output(
            ["wmic", "csproduct", "get", "uuid"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        )
        lines = [ln.strip() for ln in output.splitlines() if ln.strip() and "UUID" not in ln.upper()]
        if lines:
            parts.append(lines[0])
    except Exception:
        pass

    raw = "|".join(_safe_text(p) for p in parts if _safe_text(p))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()


def get_request_code():
    digest = hashlib.sha256(get_machine_fingerprint().encode("utf-8")).digest()
    code = base64.b32encode(digest).decode("ascii").replace("=", "")
    return code[:16]


def _hmac_token(payload, master_key):
    sign = hmac.new(master_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    token = base64.b32encode(sign).decode("ascii").replace("=", "")
    return token[:20]


def generate_license_key(request_code, expires_yyyymmdd, master_key):
    request_code = _safe_text(request_code).upper()
    expires_yyyymmdd = _safe_text(expires_yyyymmdd)
    payload = f"{request_code}|{expires_yyyymmdd}"
    token = _hmac_token(payload, master_key)
    return f"OF39-{expires_yyyymmdd}-{token}"


def validate_license_key(license_key, master_key, request_code=None):
    key = _safe_text(license_key).upper()
    if not key.startswith("OF39-"):
        return False, "Formato de chave invalido."

    parts = key.split("-")
    if len(parts) != 3:
        return False, "Formato de chave invalido."

    _, expires_yyyymmdd, token = parts
    if len(expires_yyyymmdd) != 8 or not expires_yyyymmdd.isdigit():
        return False, "Data de validade invalida."

    try:
        expiry = datetime.strptime(expires_yyyymmdd, "%Y%m%d").date()
    except Exception:
        return False, "Data de validade invalida."

    if datetime.now().date() > expiry:
        return False, "Licenca expirada."

    req_code = (request_code or get_request_code()).upper()
    expected = _hmac_token(f"{req_code}|{expires_yyyymmdd}", master_key)
    if token != expected:
        return False, "Chave nao corresponde a este computador."

    return True, "Licenca valida."


def load_license_file(path=LICENSE_FILE_DEFAULT):
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _safe_text(data.get("license_key"))
    except Exception:
        return ""


def save_license_file(license_key, path=LICENSE_FILE_DEFAULT):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"license_key": _safe_text(license_key)}, f, ensure_ascii=True, indent=2)


def get_master_key():
    return _safe_text(os.environ.get("OFICINA_MASTER_KEY")) or MASTER_KEY_DEFAULT
