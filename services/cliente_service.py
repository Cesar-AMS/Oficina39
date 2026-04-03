from __future__ import annotations

from extensions import db
from models import Cliente
from repositories import cliente_repository
from services.integration_service import consultar_cep, consultar_placa
from services.validacao_service import ValidacaoService
from services.webhook_service import disparar_evento_webhook, payload_cliente
from utils.formatters import somente_digitos, texto_limpo


CLIENT_FIELDS = [
    "nome_cliente",
    "cpf",
    "telefone",
    "email",
    "endereco",
    "cidade",
    "estado",
    "cep",
    "placa",
    "fabricante",
    "modelo",
    "ano",
    "motor",
    "combustivel",
    "cor",
    "tanque",
    "km",
    "direcao",
    "ar",
]


def list_clients():
    return cliente_repository.listar_todos()


def get_client(client_id: int):
    return cliente_repository.buscar_por_id(client_id)


def search_clients(term: str, limit: int = 20):
    return cliente_repository.buscar_por_termo(term, limite=limit)


def lookup_cep(cep: str) -> dict:
    return consultar_cep(cep)


def lookup_plate(placa: str) -> dict:
    return consultar_placa(placa)


def _clean_payload(data: dict) -> dict:
    cleaned = {}
    for field in CLIENT_FIELDS:
        value = data.get(field)
        if field == "cpf":
            cleaned[field] = somente_digitos(value)
        elif field == "cep":
            cleaned[field] = somente_digitos(value)
        elif field == "telefone":
            cleaned[field] = texto_limpo(value)
        elif field == "placa":
            cleaned[field] = texto_limpo(value).upper()
        elif field == "estado":
            cleaned[field] = texto_limpo(value).upper()[:2]
        elif field == "km":
            try:
                cleaned[field] = int(value or 0)
            except (TypeError, ValueError):
                cleaned[field] = 0
        else:
            cleaned[field] = texto_limpo(value)
    return cleaned


def _validate_payload(data: dict, *, current_client_id: int | None = None) -> dict:
    cleaned = _clean_payload(data)

    if not cleaned["nome_cliente"]:
        raise ValueError("Nome e obrigatorio.")

    cpf = cleaned["cpf"]
    if not cpf:
        raise ValueError("CPF e obrigatorio.")
    if len(cpf) != 11:
        raise ValueError("CPF deve ter 11 digitos.")
    if not ValidacaoService.validar_cpf(cpf):
        raise ValueError("CPF invalido.")

    existing = cliente_repository.buscar_por_cpf(cpf)
    if existing and existing.id != current_client_id:
        raise ValueError("CPF ja cadastrado.")

    telefone = cleaned["telefone"]
    if not telefone:
        raise ValueError("Telefone e obrigatorio.")
    if not ValidacaoService.validar_telefone(telefone):
        raise ValueError("Telefone invalido.")

    email = cleaned["email"]
    if email and not ValidacaoService.validar_email(email):
        raise ValueError("E-mail invalido.")

    cep = cleaned["cep"]
    if cep and len(cep) != 8:
        raise ValueError("CEP invalido. Informe 8 digitos.")

    placa = cleaned["placa"]
    if placa and not ValidacaoService.validar_placa(placa):
        raise ValueError("Placa invalida.")

    ano = cleaned["ano"]
    if ano and not ValidacaoService.validar_ano(ano):
        raise ValueError("Ano invalido.")

    km = cleaned["km"]
    if km and not ValidacaoService.validar_km(km):
        raise ValueError("KM invalido.")

    return cleaned


def create_client(data: dict):
    cleaned = _validate_payload(data)
    client = Cliente(**cleaned)
    db.session.add(client)
    db.session.commit()
    disparar_evento_webhook('cliente.criado', payload_cliente(client))
    return client


def update_client(client_id: int, data: dict):
    client = get_client(client_id)
    if not client:
        raise LookupError("Cliente nao encontrado.")

    merged = {field: getattr(client, field, None) for field in CLIENT_FIELDS}
    merged.update(data or {})
    cleaned = _validate_payload(merged, current_client_id=client_id)

    for field, value in cleaned.items():
        setattr(client, field, value)

    db.session.commit()
    return client


def delete_client(client_id: int) -> None:
    client = get_client(client_id)
    if not client:
        raise LookupError("Cliente nao encontrado.")
    db.session.delete(client)
    db.session.commit()
