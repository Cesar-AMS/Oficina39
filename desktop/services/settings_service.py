from __future__ import annotations

import os
import shutil
import uuid
import json
from pathlib import Path

from desktop.infrastructure.asset_paths import project_root, resolve_public_path
from desktop.repositories.config_repository import get_current_config
from desktop.repositories.order_repository import list_active_professionals
from extensions import db
from infrastructure.backup_service import criar_backup_database, status_backups
from infrastructure.export_service import ExportService
from infrastructure.export_service import pd as pandas_module
from models import Profissional
from repositories import config_repository as legacy_config_repository
from repositories import profissional_repository
from services.config_service import salvar_config_contador
from services.validacao_service import ValidacaoService
from utils.formatters import cnpj_sem_mascara, somente_digitos, texto_limpo


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
BRANDING_FIELDS = {"logo", "qrcode1", "qrcode2"}


def _branding_upload_dir() -> str:
    path = os.path.join(project_root(), "static", "uploads", "branding")
    os.makedirs(path, exist_ok=True)
    return path


def _public_branding_path(filename: str) -> str:
    return f"/static/uploads/branding/{filename}"


def _validate_email(value: str, field_name: str) -> None:
    if value and not ValidacaoService.validar_email(value):
        raise ValueError(f"{field_name} invalido.")


def _validate_phone(value: str, field_name: str) -> None:
    digits = somente_digitos(value)
    if digits and not ValidacaoService.validar_telefone(digits):
        raise ValueError(f"{field_name} invalido.")


def _text(value) -> str:
    return texto_limpo(value)


def _config_defaults() -> dict:
    return {
        "email_cliente": "",
        "senha_app": "",
        "email_contador": "",
        "profissional_envio_auto": "",
        "frequencia": "diario",
        "dia_envio": 1,
        "ativo": True,
        "cep_provider_ativo": "",
        "cep_provider_primario": "",
        "cep_api_key_primaria": "",
        "cep_provider_secundario": "",
        "cep_api_key_secundaria": "",
        "placa_provider_ativo": "",
        "placa_provider_primario": "",
        "placa_api_key_primaria": "",
        "placa_provider_secundario": "",
        "placa_api_key_secundaria": "",
        "whatsapp_orcamento": "",
        "nome_exibicao_sistema": "",
        "empresa_nome": "",
        "empresa_email": "",
        "empresa_telefone": "",
        "empresa_endereco": "",
        "tema_visual": "escuro",
        "logo_index_path": "",
        "logo_index_formato": "circulo",
        "logo_index_escala": 1.0,
        "logo_index_offset_x": 0.0,
        "logo_index_offset_y": 0.0,
        "qrcode_1_path": "",
        "qrcode_2_path": "",
    }


def list_professional_names() -> list[str]:
    names = []
    for professional in list_active_professionals():
        name = _text(getattr(professional, "nome", ""))
        if name and name not in names:
            names.append(name)
    return names


def load_settings() -> dict:
    defaults = _config_defaults()
    config = get_current_config()
    if config:
        defaults.update(config.to_dict_completo())

    defaults["logo_local_path"] = resolve_public_path(defaults.get("logo_index_path"))
    defaults["qrcode_1_local_path"] = resolve_public_path(defaults.get("qrcode_1_path"))
    defaults["qrcode_2_local_path"] = resolve_public_path(defaults.get("qrcode_2_path"))
    defaults["profissionais"] = list_professional_names()
    return defaults


def store_branding_asset(source_path: str, kind: str) -> str:
    if kind not in BRANDING_FIELDS:
        raise ValueError("Tipo de branding invalido.")
    if not source_path or not os.path.exists(source_path):
        raise FileNotFoundError("Arquivo de imagem nao encontrado.")

    extension = os.path.splitext(source_path)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Formato invalido. Use PNG, JPG, JPEG, WEBP, GIF ou BMP.")

    prefix = {
        "logo": "cliente_logo",
        "qrcode1": "cliente_qrcode_1",
        "qrcode2": "cliente_qrcode_2",
    }[kind]
    filename = f"{prefix}_{uuid.uuid4().hex[:12]}{extension}"
    destination = os.path.join(_branding_upload_dir(), filename)
    shutil.copy2(source_path, destination)
    return _public_branding_path(filename)


def save_settings(payload: dict) -> dict:
    data = dict(payload or {})

    data["email_cliente"] = _text(data.get("email_cliente"))
    data["email_contador"] = _text(data.get("email_contador"))
    data["empresa_email"] = _text(data.get("empresa_email"))
    data["empresa_telefone"] = _text(data.get("empresa_telefone"))
    data["whatsapp_orcamento"] = somente_digitos(data.get("whatsapp_orcamento"))
    data["empresa_nome"] = _text(data.get("empresa_nome"))
    data["empresa_endereco"] = _text(data.get("empresa_endereco"))
    data["nome_exibicao_sistema"] = _text(data.get("nome_exibicao_sistema"))
    data["tema_visual"] = (_text(data.get("tema_visual")) or "escuro").lower()
    data["logo_index_formato"] = _text(data.get("logo_index_formato")) or "circulo"
    data["profissional_envio_auto"] = _text(data.get("profissional_envio_auto"))
    data["cep_provider_ativo"] = _text(data.get("cep_provider_ativo"))
    data["cep_provider_primario"] = _text(data.get("cep_provider_primario"))
    data["cep_provider_secundario"] = _text(data.get("cep_provider_secundario"))
    data["placa_provider_ativo"] = _text(data.get("placa_provider_ativo"))
    data["placa_provider_primario"] = _text(data.get("placa_provider_primario"))
    data["placa_provider_secundario"] = _text(data.get("placa_provider_secundario"))
    if data["tema_visual"] not in {"escuro", "claro"}:
        data["tema_visual"] = "escuro"

    _validate_email(data["email_cliente"], "E-mail do cliente")
    _validate_email(data["email_contador"], "E-mail do contador")
    _validate_email(data["empresa_email"], "E-mail da empresa")
    _validate_phone(data["empresa_telefone"], "Telefone da empresa")

    config = salvar_config_contador(data)
    result = config.to_dict_completo()
    result["logo_local_path"] = resolve_public_path(result.get("logo_index_path"))
    result["qrcode_1_local_path"] = resolve_public_path(result.get("qrcode_1_path"))
    result["qrcode_2_local_path"] = resolve_public_path(result.get("qrcode_2_path"))
    result["profissionais"] = list_professional_names()
    return result


def list_professionals() -> list[dict]:
    return [item.to_dict() for item in profissional_repository.listar(ativos_apenas=False)]


def create_professional(name: str, cnpj: str, active: bool = True) -> dict:
    clean_name = _text(name)
    clean_cnpj = cnpj_sem_mascara(cnpj)

    if not clean_name or not clean_cnpj:
        raise ValueError("Nome e CNPJ sao obrigatorios.")
    if not ValidacaoService.validar_cnpj(clean_cnpj):
        raise ValueError("CNPJ invalido.")
    if profissional_repository.buscar_por_nome(clean_name):
        raise ValueError("Ja existe profissional com este nome.")
    if profissional_repository.buscar_por_cnpj(clean_cnpj):
        raise ValueError("Ja existe profissional com este CNPJ.")

    professional = Profissional(nome=clean_name, cnpj=clean_cnpj, ativo=bool(active))
    db.session.add(professional)
    db.session.commit()
    return professional.to_dict()


def remove_professional(professional_id: int) -> None:
    professional = profissional_repository.buscar_por_id(professional_id)
    if not professional:
        raise LookupError("Profissional nao encontrado.")
    db.session.delete(professional)
    db.session.commit()


def get_backup_status() -> dict:
    data = status_backups(prefixo="database_backup_", extensao=".db")
    data["backup_dir"] = os.path.join(project_root(), "backups")
    return data


def run_database_backup() -> dict:
    return criar_backup_database(prefixo="database_backup_", dias_retencao=15)


def default_export_filename(export_type: str, export_format: str) -> str:
    return ExportService.get_nome_arquivo(export_type, export_format)


def export_data_to_file(export_type: str, export_format: str, destination_path: str) -> str:
    export_type = (export_type or "completo").strip().lower()
    export_format = (export_format or "db").strip().lower()
    destination = os.path.abspath(destination_path)

    if export_format == "db":
        if export_type != "completo":
            raise ValueError("Exportacao .db disponivel apenas para banco completo.")
        shutil.copy2(ExportService.get_database_path(), destination)
        return destination

    if export_format == "csv":
        content = ExportService.exportar_csv(export_type).getvalue()
        with open(destination, "w", encoding="utf-8-sig", newline="") as handle:
            handle.write(content)
        return destination

    if export_format == "json":
        content = ExportService.exportar_json(export_type)
        with open(destination, "w", encoding="utf-8") as handle:
            json.dump(content, handle, ensure_ascii=False, indent=2)
        return destination

    if export_format == "xlsx":
        content = ExportService.exportar_excel(export_type)
        with open(destination, "wb") as handle:
            handle.write(content.getvalue())
        return destination

    raise ValueError("Formato de exportacao invalido.")


def list_report_history(limit: int = 20) -> list[dict]:
    return [item.to_dict() for item in legacy_config_repository.listar_envios(limit)]


def list_audit_history(limit: int = 50) -> list[dict]:
    return [item.to_dict() for item in legacy_config_repository.listar_auditoria_eventos(limit)]


def import_data_from_file(import_type: str, source_path: str) -> dict:
    import_type = (import_type or "clientes").strip().lower()
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError("Arquivo de importacao nao encontrado.")

    extension = source.suffix.lower()
    if extension == ".json":
        with source.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        result = ExportService.importar_json(data, import_type)
    elif extension == ".csv":
        if pandas_module is None:
            raise RuntimeError("pandas nao instalado. Nao e possivel importar CSV.")
        dataframe = pandas_module.read_csv(str(source), sep=None, engine="python")
        result = ExportService.importar_tabular(dataframe, import_type)
    elif extension == ".xlsx":
        if pandas_module is None:
            raise RuntimeError("pandas nao instalado. Nao e possivel importar XLSX.")
        dataframe = pandas_module.read_excel(str(source))
        result = ExportService.importar_tabular(dataframe, import_type)
    else:
        raise ValueError("Formato de arquivo invalido. Use JSON, CSV ou XLSX.")

    db.session.commit()
    return result
