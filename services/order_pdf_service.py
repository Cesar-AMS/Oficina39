from __future__ import annotations

import io
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace

from extensions import db

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    PDF_AVAILABLE = True
    PDF_IMPORT_ERROR = None
except ImportError as exc:
    PDF_AVAILABLE = False
    PDF_IMPORT_ERROR = exc


def pdf_available() -> bool:
    return PDF_AVAILABLE


def ensure_pdf_available() -> None:
    if PDF_AVAILABLE:
        return
    raise RuntimeError(f"Biblioteca ReportLab nao instalada: {PDF_IMPORT_ERROR}")


def suggested_order_pdf_name(order_id: int) -> str:
    return f"recibo_ordem_{order_id}.pdf"


def suggested_preview_pdf_name() -> str:
    return "orcamento_preliminar.pdf"


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _static_root() -> str:
    return os.path.join(_project_root(), "static")


def _resolve_branding_path(path_value: str | None) -> str | None:
    value = (path_value or "").strip()
    if not value:
        return None

    candidates: list[str] = []
    if os.path.isabs(value):
        candidates.append(value)
    else:
        normalized = value.replace("/", os.sep).lstrip(os.sep)
        static_prefix = f"static{os.sep}"
        if normalized.lower().startswith(static_prefix.lower()):
            relative_static = normalized[len(static_prefix):]
            candidates.append(os.path.join(_static_root(), relative_static))
        candidates.append(os.path.join(_project_root(), normalized))
        candidates.append(os.path.abspath(normalized))

    for candidate in candidates:
        real_path = os.path.abspath(candidate)
        if os.path.exists(real_path):
            return real_path
    return None


def _prepare_pdf_image(image_path, trim_white_borders=False):
    if not trim_white_borders:
        return image_path, None

    try:
        from PIL import Image as PILImage, ImageChops

        image = PILImage.open(image_path).convert("RGB")
        background = PILImage.new("RGB", image.size, "white")
        diff = ImageChops.difference(image, background)
        bbox = diff.getbbox()
        if not bbox:
            return image_path, None

        original_w, original_h = image.size
        bbox_w = bbox[2] - bbox[0]
        bbox_h = bbox[3] - bbox[1]
        if bbox_w >= original_w * 0.96 and bbox_h >= original_h * 0.96:
            return image_path, None

        cropped = image.crop(bbox)
        buffer = io.BytesIO()
        cropped.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer, buffer
    except Exception:
        return image_path, None


def _create_pdf_image(image_path, max_width, max_height, scale=1.0, trim_white_borders=False):
    if not image_path or not os.path.exists(image_path):
        return None

    try:
        scale = min(3.0, max(0.7, float(scale or 1.0)))
    except (TypeError, ValueError):
        scale = 1.0

    try:
        image_source, temp_buffer = _prepare_pdf_image(image_path, trim_white_borders)
        reader = ImageReader(image_source)
        img_w, img_h = reader.getSize()
        if not img_w or not img_h:
            raise ValueError("Imagem invalida")

        target_w = float(max_width) * scale
        target_h = float(max_height) * scale
        ratio = min(target_w / float(img_w), target_h / float(img_h))
        final_w = img_w * ratio
        final_h = img_h * ratio

        image = Image(image_source, width=final_w, height=final_h)
        image.hAlign = "LEFT"
        if temp_buffer is not None:
            image._image_buffer = temp_buffer
        return image
    except Exception:
        image = Image(image_path, width=max_width * scale, height=max_height * scale)
        image.hAlign = "LEFT"
        return image


def _get_branding():
    from models import ConfigContador

    config = ConfigContador.query.first()
    default_logo = _resolve_branding_path("/static/images/picapau4.png") or _resolve_branding_path("imagemlogopicapau.png")
    default_qr_1 = _resolve_branding_path("/static/images/qrcodewhatsapp.jpeg")
    default_qr_2 = _resolve_branding_path("/static/images/qrcodeinstagram.jpeg")

    branding = {
        "logo_path": default_logo,
        "empresa_nome": "OFICINA 39",
        "empresa_telefone": "(11) 99209-2341",
        "empresa_email": "oficina39ca@gmail.com",
        "empresa_endereco": "Rua Noel Rosa, 39 - Poa - SP",
        "qrcode_1_path": default_qr_1,
        "qrcode_2_path": default_qr_2,
        "logo_escala": 1.0,
    }

    if not config:
        return branding

    branding["empresa_nome"] = ((config.empresa_nome or "").strip() or (config.nome_exibicao_sistema or "").strip() or branding["empresa_nome"])
    branding["empresa_telefone"] = (config.empresa_telefone or "").strip() or branding["empresa_telefone"]
    branding["empresa_email"] = (config.empresa_email or "").strip() or branding["empresa_email"]
    branding["empresa_endereco"] = (config.empresa_endereco or "").strip() or branding["empresa_endereco"]

    try:
        branding["logo_escala"] = min(3.0, max(0.7, float(config.logo_index_escala or 1.0)))
    except (TypeError, ValueError):
        branding["logo_escala"] = 1.0

    if (config.logo_index_path or "").strip():
        resolved = _resolve_branding_path(config.logo_index_path)
        if resolved:
            branding["logo_path"] = resolved

    for key in ("qrcode_1_path", "qrcode_2_path"):
        value = (getattr(config, key, None) or "").strip()
        if value:
            resolved = _resolve_branding_path(value)
            if resolved:
                branding[key] = resolved

    return branding


def _widths(total_width, proportions):
    total = float(sum(proportions))
    return [(total_width * value) / total for value in proportions]


def _parse_decimal(value) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))

    text = str(value).strip()
    if not text:
        return Decimal("0")

    cleaned = (
        text.replace("R$", "")
        .replace("r$", "")
        .replace(" ", "")
    )

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def _parse_float(value) -> float:
    return float(_parse_decimal(value))


def _money(value) -> str:
    amount = _parse_decimal(value).quantize(Decimal("0.01"))
    return f"R$ {amount:.2f}".replace(".", ",")


def _decimal_text(value, casas: str = "0.01") -> str:
    amount = _parse_decimal(value).quantize(Decimal(casas))
    return f"{amount:.2f}".replace(".", ",")


def _quantity_text(value) -> str:
    amount = _parse_decimal(value).quantize(Decimal("0.01"))
    if amount == amount.to_integral():
        return str(int(amount))
    return f"{amount:.2f}".replace(".", ",")


def _coalesce_text(*values):
    for value in values:
        texto = str(value or "").strip()
        if texto:
            return texto
    return ""


def _normalizar_data_preview(valor):
    if not valor:
        return None
    if isinstance(valor, datetime):
        return valor
    texto = str(valor).strip()
    for formato in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(texto[:19], formato)
        except ValueError:
            continue
    return None


def _montar_cliente_preview(dados: dict):
    from models import Cliente

    cliente = None
    cliente_id = (dados or {}).get("cliente_id")
    if cliente_id not in (None, ""):
        try:
            cliente = db.session.get(Cliente, int(cliente_id))
        except Exception:
            cliente = None

    cliente_payload = (dados or {}).get("cliente") or {}
    if cliente is None:
        return SimpleNamespace(
            id=cliente_payload.get("id"),
            nome_cliente=_coalesce_text(cliente_payload.get("nome_cliente"), dados.get("cliente_nome")),
            cpf=_coalesce_text(cliente_payload.get("cpf"), dados.get("cpf")),
            telefone=_coalesce_text(cliente_payload.get("telefone"), dados.get("telefone")),
            email=_coalesce_text(cliente_payload.get("email"), dados.get("email")),
            endereco=_coalesce_text(cliente_payload.get("endereco"), dados.get("endereco")),
            cidade=_coalesce_text(cliente_payload.get("cidade"), dados.get("cidade")),
            estado=_coalesce_text(cliente_payload.get("estado"), dados.get("estado")),
            cep=_coalesce_text(cliente_payload.get("cep"), dados.get("cep")),
            placa=_coalesce_text(cliente_payload.get("placa"), dados.get("placa")),
            fabricante=_coalesce_text(cliente_payload.get("fabricante"), dados.get("fabricante")),
            modelo=_coalesce_text(cliente_payload.get("modelo"), dados.get("modelo")),
            ano=_coalesce_text(cliente_payload.get("ano"), dados.get("ano")),
            motor=_coalesce_text(cliente_payload.get("motor"), dados.get("motor")),
            combustivel=_coalesce_text(cliente_payload.get("combustivel"), dados.get("combustivel")),
            cor=_coalesce_text(cliente_payload.get("cor"), dados.get("cor")),
            tanque=_coalesce_text(cliente_payload.get("tanque"), dados.get("tanque")),
            km=int(cliente_payload.get("km") or dados.get("km") or 0),
            direcao=_coalesce_text(cliente_payload.get("direcao"), dados.get("direcao")),
            ar=_coalesce_text(cliente_payload.get("ar"), dados.get("ar")),
        )
    return cliente


def _montar_itens_servico_preview(servicos: list[dict]):
    itens = []
    for idx, item in enumerate(servicos or [], start=1):
        valor = _parse_float(item.get("valor_servico") or item.get("valor") or 0)
        itens.append(SimpleNamespace(
            id=idx,
            codigo_servico=_coalesce_text(item.get("codigo_servico"), item.get("codigo")),
            descricao_servico=_coalesce_text(item.get("descricao_servico"), item.get("descricao")),
            valor_servico=valor,
            nome_profissional=_coalesce_text(item.get("nome_profissional"), item.get("profissional")),
        ))
    return itens


def _montar_itens_peca_preview(pecas: list[dict]):
    itens = []
    for idx, item in enumerate(pecas or [], start=1):
        quantidade = _parse_float(item.get("quantidade") or 0)
        valor_unitario = round(_parse_float(item.get("valor_unitario") or 0), 2)
        itens.append(SimpleNamespace(
            id=idx,
            codigo_peca=_coalesce_text(item.get("codigo_peca"), item.get("codigo")),
            descricao_peca=_coalesce_text(item.get("descricao_peca"), item.get("descricao")),
            quantidade=round(quantidade, 2),
            valor_unitario=valor_unitario,
        ))
    return itens


def _montar_preview_order(dados: dict, client):
    servicos = _montar_itens_servico_preview((dados or {}).get("servicos") or [])
    pecas = _montar_itens_peca_preview((dados or {}).get("pecas") or [])
    total_servicos = round(sum(float(item.valor_servico or 0) for item in servicos), 2)
    total_pecas = round(sum(float(item.quantidade or 0) * float(item.valor_unitario or 0) for item in pecas), 2)
    total_geral = round(total_servicos + total_pecas, 2)
    desconto_percentual = _parse_float((dados or {}).get("desconto_percentual") or 0)
    desconto_valor = _parse_float((dados or {}).get("desconto_valor") or 0)
    if desconto_valor <= 0 and desconto_percentual > 0:
        desconto_valor = round(total_geral * (desconto_percentual / 100), 2)
    total_cobrado = round(max(0, total_geral - desconto_valor), 2)
    total_pago = _parse_float((dados or {}).get("total_pago") or 0)

    return SimpleNamespace(
        id=(dados or {}).get("id") or "PREVIEW",
        cliente_id=getattr(client, "id", None),
        cliente=client,
        diagnostico=_coalesce_text((dados or {}).get("diagnostico")),
        observacao_interna=_coalesce_text((dados or {}).get("observacao_interna")),
        profissional_responsavel=_coalesce_text((dados or {}).get("profissional_responsavel")),
        assinatura_cliente=_coalesce_text((dados or {}).get("assinatura_cliente")),
        status=_coalesce_text((dados or {}).get("status")) or "Aguardando",
        forma_pagamento=_coalesce_text((dados or {}).get("forma_pagamento")) or "Nao informado",
        data_entrada=_normalizar_data_preview((dados or {}).get("data_entrada")) or datetime.now(),
        data_emissao=_normalizar_data_preview((dados or {}).get("data_emissao")) or datetime.now(),
        data_retirada=_normalizar_data_preview((dados or {}).get("data_retirada")),
        data_conclusao=_normalizar_data_preview((dados or {}).get("data_conclusao")),
        desconto_percentual=desconto_percentual,
        desconto_valor=desconto_valor,
        debito_vencimento=(dados or {}).get("debito_vencimento"),
        debito_observacao=_coalesce_text((dados or {}).get("debito_observacao")),
        total_servicos=total_servicos,
        total_pecas=total_pecas,
        total_geral=total_geral,
        total_cobrado=total_cobrado,
        total_pago=total_pago,
        saldo_pendente=round(max(0, total_cobrado - total_pago), 2),
        status_financeiro=_coalesce_text((dados or {}).get("status_financeiro")) or (
            "Quitado" if total_cobrado and total_pago + 0.0001 >= total_cobrado
            else ("Parcial" if total_pago > 0 else "Em aberto")
        ),
        servicos=servicos,
        pecas=pecas,
        pagamentos=[],
    )


def _build_order_pdf_bytes(order, client, document_title: str | None = None) -> bytes:
    ensure_pdf_available()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )
    content_width = doc.width
    elements = []
    styles = getSampleStyleSheet()

    logo_size = 30 * mm
    qr_size = 23 * mm
    qr_gap = 4 * mm

    style_company = ParagraphStyle(
        "Company",
        parent=styles["Normal"],
        fontSize=20,
        textColor=colors.HexColor("#0a3147"),
        fontName="Helvetica-Bold",
        alignment=1,
        leading=23,
        spaceAfter=5,
    )
    style_company_data = ParagraphStyle(
        "CompanyData",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#444444"),
        alignment=1,
        leading=14,
    )
    style_title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=17,
        textColor=colors.HexColor("#c44536"),
        fontName="Helvetica-Bold",
        alignment=1,
        leading=20,
        spaceAfter=10,
        spaceBefore=7,
    )
    style_section = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#0a3147"),
        fontName="Helvetica-Bold",
        spaceAfter=5,
        spaceBefore=8,
    )
    style_normal = ParagraphStyle(
        "NormalBody",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#333333"),
        leading=14,
    )
    style_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#0a3147"),
        fontName="Helvetica-Bold",
        leading=14,
    )
    style_value = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#27ae60"),
        fontName="Helvetica-Bold",
        alignment=2,
    )
    style_total = ParagraphStyle(
        "Total",
        parent=styles["Normal"],
        fontSize=14,
        textColor=colors.HexColor("#c44536"),
        fontName="Helvetica-Bold",
        alignment=2,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#999999"),
        alignment=1,
    )

    branding = _get_branding()
    logo_path = branding.get("logo_path") or ""
    if logo_path and os.path.exists(logo_path):
        logo = _create_pdf_image(
            logo_path,
            logo_size,
            logo_size,
            branding.get("logo_escala", 1.0),
            trim_white_borders=True,
        )
        logo_block = Table([[logo]], colWidths=[logo_size], hAlign="LEFT")
        logo_block.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), -1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
    else:
        logo_block = Paragraph("OF39", ParagraphStyle("LogoFallback", fontSize=18))

    company_name = Paragraph(branding["empresa_nome"], style_company)
    company_lines = []
    if branding["empresa_endereco"]:
        company_lines.append(branding["empresa_endereco"])
    contact_line = " | ".join(
        part for part in [
            f"Tel: {branding['empresa_telefone']}" if branding["empresa_telefone"] else "",
            f"E-mail: {branding['empresa_email']}" if branding["empresa_email"] else "",
        ] if part
    )
    if contact_line:
        company_lines.append(contact_line)
    company_data = Paragraph("<br/>".join(company_lines) or "&nbsp;", style_company_data)
    company_block = Table([[company_name], [company_data]], hAlign="CENTER")
    company_block.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    qr_images = []
    for qr_path in [branding.get("qrcode_1_path") or "", branding.get("qrcode_2_path") or ""]:
        if qr_path and os.path.exists(qr_path):
            qr_images.append(_create_pdf_image(qr_path, qr_size, qr_size))

    if qr_images:
        qr_table = Table([qr_images], colWidths=[qr_size] * len(qr_images))
        qr_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
    else:
        qr_table = Paragraph("", style_normal)

    qr_width = (len(qr_images) * qr_size) + (max(0, len(qr_images) - 1) * qr_gap)
    qr_width = qr_width if qr_width > 0 else 28 * mm
    logo_width = 47 * mm
    company_width = max(77 * mm, content_width - logo_width - qr_width)

    header = Table([[logo_block, company_block, qr_table]], colWidths=[logo_width, company_width, qr_width], hAlign="LEFT")
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (0, -1), 14),
        ("LEFTPADDING", (1, 0), (1, -1), 12),
        ("RIGHTPADDING", (1, 0), (1, -1), 12),
        ("LEFTPADDING", (2, 0), (2, -1), 8),
    ]))
    elements.append(header)

    separator = Table([[""]], colWidths=[content_width], hAlign="LEFT")
    separator.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#d9d9d9")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(separator)
    elements.append(Spacer(1, 4 * mm))

    resolved_title = (document_title or "").strip() or f"ORDEM DE SERVICO #{order.id}"
    elements.append(Paragraph(resolved_title, style_title))
    elements.append(Spacer(1, 5 * mm))

    client_rows = [
        [Paragraph("Cliente:", style_label), Paragraph(client.nome_cliente or "---", style_normal)],
        [Paragraph("CPF:", style_label), Paragraph(client.cpf or "---", style_normal)],
    ]
    vehicle = f"{client.fabricante or ''} {client.modelo or ''} - {client.placa or ''} - {client.ano or ''} {client.cor or ''}".strip()
    if vehicle and vehicle != "- - -":
        client_rows.append([Paragraph("Veiculo:", style_label), Paragraph(vehicle, style_normal)])
    client_rows.append([Paragraph("Profissional:", style_label), Paragraph(order.profissional_responsavel or "---", style_normal)])

    client_table = Table(client_rows, colWidths=_widths(content_width, [32, 158]), hAlign="LEFT")
    client_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8f9fb")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 4 * mm))

    elements.append(Paragraph("SERVICOS REALIZADOS", style_section))
    if order.servicos:
        data = [["Codigo", "Descricao", "Valor"]]
        for service in order.servicos:
            data.append([service.codigo_servico or "---", service.descricao_servico or "---", _money(service.valor_servico)])
        services_table = Table(data, colWidths=_widths(content_width, [24, 116, 50]), hAlign="LEFT")
        services_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a3147")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "LEFT"),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(services_table)
    else:
        elements.append(Paragraph("Nenhum servico registrado", style_normal))
    elements.append(Spacer(1, 5 * mm))

    elements.append(Paragraph("PECAS UTILIZADAS", style_section))
    if order.pecas:
        data = [["Codigo", "Descricao", "Qtd", "Valor Unit.", "Total"]]
        for part in order.pecas:
            total = float(part.quantidade or 0) * float(part.valor_unitario or 0)
            data.append([
                part.codigo_peca or "---",
                part.descricao_peca or "---",
                _quantity_text(part.quantidade),
                _money(part.valor_unitario),
                _money(total),
            ])
        parts_table = Table(data, colWidths=_widths(content_width, [24, 92, 18, 28, 28]), hAlign="LEFT")
        parts_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a3147")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "LEFT"),
            ("ALIGN", (2, 1), (4, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(parts_table)
    else:
        elements.append(Paragraph("Nenhuma peca registrada", style_normal))
    elements.append(Spacer(1, 8 * mm))

    discount_value = float(getattr(order, "desconto_valor", 0) or 0)
    total_paid = float(getattr(order, "total_pago", 0) or 0)
    pending = float(getattr(order, "saldo_pendente", 0) or 0)
    final_total = float(getattr(order, "total_cobrado", order.total_geral) or 0)

    summary_rows = [
        [Paragraph("Total Servicos:", style_normal), Paragraph(_money(order.total_servicos), style_value)],
        [Paragraph("Total Pecas:", style_normal), Paragraph(_money(order.total_pecas), style_value)],
    ]
    if discount_value > 0.009:
        summary_rows.append([Paragraph("Desconto aplicado:", style_normal), Paragraph(_money(discount_value), style_value)])
    if total_paid > 0.009:
        summary_rows.append([Paragraph("Total pago:", style_normal), Paragraph(_money(total_paid), style_value)])
    if pending > 0.009:
        summary_rows.append([Paragraph("Saldo pendente:", style_normal), Paragraph(_money(pending), style_value)])
    summary_rows.append([Paragraph("TOTAL FINAL DA VENDA:", style_total), Paragraph(_money(final_total), style_total)])

    summary_table = Table(summary_rows, colWidths=_widths(content_width, [140, 50]), hAlign="LEFT")
    summary_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, 0), (1, 0), 0.5, colors.HexColor("#dddddd")),
        ("LINEABOVE", (0, -1), (1, -1), 0.75, colors.HexColor("#dddddd")),
        ("TOPPADDING", (0, 0), (1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (1, -1), 4),
        ("BACKGROUND", (0, 0), (1, -2), colors.HexColor("#f8f9fb")),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 8 * mm))

    payments = getattr(order, "pagamentos", []) or []
    if pending > 0.009 or payments:
        elements.append(Paragraph("SITUACAO FINANCEIRA", style_section))
    if pending > 0.009:
        debit_details = [f"<b>Valor restante em aberto:</b> {_money(pending)}"]
        if getattr(order, "debito_vencimento", None):
            debit_details.append(f"<b>Vencimento:</b> {order.debito_vencimento.strftime('%d/%m/%Y')}")
        if getattr(order, "debito_observacao", None):
            debit_details.append(f"<b>Observacao do debito:</b> {order.debito_observacao}")
        elements.append(Paragraph("<br/>".join(debit_details), style_normal))
        elements.append(Spacer(1, 3 * mm))

    if payments:
        payment_rows = [["Data", "Forma", "Valor", "Observacao"]]
        for payment in payments:
            payment_rows.append([
                payment.data_pagamento.strftime("%d/%m/%Y %H:%M") if getattr(payment, "data_pagamento", None) else "---",
                payment.forma_pagamento or "---",
                _money(payment.valor),
                payment.observacao or "---",
            ])
        payment_table = Table(payment_rows, colWidths=_widths(content_width, [34, 30, 26, 100]), hAlign="LEFT")
        payment_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a3147")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (0, 1), (1, -1), "CENTER"),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("ALIGN", (3, 1), (3, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(payment_table)
    else:
        elements.append(Paragraph("Nenhum pagamento registrado", style_normal))
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("ASSINATURA DO CLIENTE", style_section))
    elements.append(Spacer(1, 6 * mm))
    if order.assinatura_cliente:
        elements.append(Paragraph(order.assinatura_cliente, style_normal))
    else:
        elements.append(Paragraph("__________________________________________________", style_normal))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph("(assinatura)", style_normal))
    elements.append(Spacer(1, 5 * mm))

    elements.append(Paragraph(f"Documento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
    elements.append(Paragraph("Obrigado pela preferencia!", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_order_pdf_bytes(order_id: int) -> bytes:
    from models import Cliente, Ordem

    order = db.session.get(Ordem, order_id)
    if not order:
        raise LookupError("Ordem nao encontrada.")

    client = db.session.get(Cliente, order.cliente_id)
    if not client:
        raise LookupError("Cliente da ordem nao encontrado.")

    return _build_order_pdf_bytes(order, client)


def generate_order_preview_pdf_bytes(dados: dict) -> bytes:
    client = _montar_cliente_preview(dados or {})
    if not _coalesce_text(getattr(client, "nome_cliente", "")):
        raise ValueError("Cliente e obrigatorio para gerar a previa do PDF.")
    order = _montar_preview_order(dados or {}, client)
    if not order.servicos and not order.pecas:
        raise ValueError("Informe ao menos um servico ou peca para gerar a previa.")
    return _build_order_pdf_bytes(order, client, document_title="ORCAMENTO")


def build_order_whatsapp_web_url(order_id: int) -> str:
    from models import ConfigContador, Ordem

    order = db.session.get(Ordem, order_id)
    if not order:
        raise LookupError("Ordem nao encontrada.")

    client = order.cliente
    config = ConfigContador.query.first()
    numero = "".join(ch for ch in str(getattr(config, "whatsapp_orcamento", "") or "") if ch.isdigit())
    if not numero:
        raise ValueError("WhatsApp da oficina nao configurado.")

    servicos = "\n".join(
        f"- {item.descricao_servico}: {_money(item.valor_servico)}"
        for item in (order.servicos or [])
    ) or "- Nenhum servico"
    pecas = "\n".join(
        f"- {item.descricao_peca}: {_money(float(item.quantidade or 0) * float(item.valor_unitario or 0))}"
        for item in (order.pecas or [])
    ) or "- Nenhuma peca"
    veiculo = " ".join(
        parte for parte in [
            getattr(client, "fabricante", "") if client else "",
            getattr(client, "modelo", "") if client else "",
        ] if str(parte or "").strip()
    ).strip()
    placa = getattr(client, "placa", "") if client else ""
    mensagem = "\n\n".join([
        f"Ola! Orcamento da OS #{order.id}",
        f"Cliente: {getattr(client, 'nome_cliente', '---') if client else '---'}",
        f"Telefone do cliente: {getattr(client, 'telefone', 'nao informado') if client else 'nao informado'}",
        f"Veiculo: {(veiculo + (' - ' + placa if placa else '')).strip() or '---'}",
        f"Profissional: {order.profissional_responsavel or '---'}",
        f"Servicos:\n{servicos}",
        f"Pecas:\n{pecas}",
        f"Total: {_money(order.total_geral)}",
    ])
    from urllib.parse import quote
    return f"https://web.whatsapp.com/send?phone={numero}&text={quote(mensagem)}"


def save_order_pdf(order_id: int, destination_path: str) -> str:
    pdf_bytes = generate_order_pdf_bytes(order_id)
    with open(destination_path, "wb") as output_file:
        output_file.write(pdf_bytes)
    return destination_path
