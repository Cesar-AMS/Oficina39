# ===========================================
# routes/export_routes.py - Recibo Profissional
# ===========================================

import traceback
import json
from flask import Blueprint, jsonify, send_file, request, Response, current_app
from extensions import db
import io
import os
from datetime import datetime, timedelta
from infrastructure.export_service import ExportService

# Tentar importar ReportLab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    PDF_AVAILABLE = True
except ImportError as e:
    PDF_AVAILABLE = False
    print(f"ReportLab nao instalado. Erro: {e}")
    print("Para instalar: pip install reportlab")

export_bp = Blueprint('export', __name__, url_prefix='/api/export')


def _resolver_caminho_branding(valor_path):
    """Converte caminhos públicos/relativos do branding para caminhos reais no disco."""
    valor = (valor_path or '').strip()
    if not valor:
        return None

    candidatos = []
    if os.path.isabs(valor):
        candidatos.append(valor)
    else:
        caminho_normalizado = valor.replace('/', os.sep).lstrip(os.sep)
        prefixo_static = f"static{os.sep}"
        if caminho_normalizado.lower().startswith(prefixo_static.lower()):
            relativo_static = caminho_normalizado[len(prefixo_static):]
            candidatos.append(os.path.join(current_app.static_folder, relativo_static))
        candidatos.append(os.path.join(current_app.root_path, caminho_normalizado))
        candidatos.append(os.path.abspath(caminho_normalizado))

    for candidato in candidatos:
        caminho_real = os.path.abspath(candidato)
        if os.path.exists(caminho_real):
            return caminho_real
    return None


def _obter_branding_empresa():
    from models import ConfigContador

    config = ConfigContador.query.first()
    # Arquivos padrão do sistema: entram apenas como fallback quando o cliente ainda não enviou branding próprio.
    logo_padrao_sistema = _resolver_caminho_branding('/static/images/picapau4.png')
    qrcode_1_padrao_sistema = _resolver_caminho_branding('/static/images/qrcodewhatsapp.jpeg')
    qrcode_2_padrao_sistema = _resolver_caminho_branding('/static/images/qrcodeinstagram.jpeg')

    logo_path = logo_padrao_sistema
    empresa_nome = 'OFICINA 39'
    empresa_telefone = '(11) 99209-2341'
    empresa_email = 'oficina39ca@gmail.com'
    empresa_endereco = 'Rua Noel Rosa, 39 - Poá - SP'
    qrcode_1_path = qrcode_1_padrao_sistema
    qrcode_2_path = qrcode_2_padrao_sistema
    logo_escala = 1.0

    if config:
        empresa_nome = (
            (config.empresa_nome or '').strip()
            or (config.nome_exibicao_sistema or '').strip()
            or empresa_nome
        )
        empresa_telefone = (config.empresa_telefone or '').strip() or empresa_telefone
        empresa_email = (config.empresa_email or '').strip() or empresa_email
        empresa_endereco = (config.empresa_endereco or '').strip() or empresa_endereco

        logo_salva = (config.logo_index_path or '').strip()
        try:
            logo_escala = min(3.0, max(0.7, float(config.logo_index_escala or 1.0)))
        except (TypeError, ValueError):
            logo_escala = 1.0
        if logo_salva:
            caminho_logo = _resolver_caminho_branding(logo_salva)
            if caminho_logo:
                logo_path = caminho_logo
        for chave, atual in (('qrcode_1_path', qrcode_1_path), ('qrcode_2_path', qrcode_2_path)):
            valor = (getattr(config, chave, None) or '').strip()
            if valor:
                caminho_qr = _resolver_caminho_branding(valor)
                if caminho_qr:
                    if chave == 'qrcode_1_path':
                        qrcode_1_path = caminho_qr
                    else:
                        qrcode_2_path = caminho_qr

    return {
        'logo_path': logo_path,
        'empresa_nome': empresa_nome,
        'empresa_telefone': empresa_telefone,
        'empresa_email': empresa_email,
        'empresa_endereco': empresa_endereco,
        'qrcode_1_path': qrcode_1_path,
        'qrcode_2_path': qrcode_2_path,
        'logo_escala': logo_escala,
    }


def _preparar_imagem_pdf(caminho_imagem, remover_bordas_brancas=False):
    if not remover_bordas_brancas:
        return caminho_imagem, None

    try:
        from PIL import Image as PILImage, ImageChops

        imagem = PILImage.open(caminho_imagem).convert('RGB')
        fundo = PILImage.new('RGB', imagem.size, 'white')
        diferenca = ImageChops.difference(imagem, fundo)
        bbox = diferenca.getbbox()
        if not bbox:
            return caminho_imagem, None

        largura_original, altura_original = imagem.size
        largura_bbox = bbox[2] - bbox[0]
        altura_bbox = bbox[3] - bbox[1]

        # So recorta quando houver borda branca significativa.
        if largura_bbox >= largura_original * 0.96 and altura_bbox >= altura_original * 0.96:
            return caminho_imagem, None

        imagem_cortada = imagem.crop(bbox)
        buffer = io.BytesIO()
        imagem_cortada.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer, buffer
    except Exception:
        return caminho_imagem, None


def _criar_logo_pdf(caminho_logo, largura_max, altura_max, escala=1.0, remover_bordas_brancas=False):
    if not os.path.exists(caminho_logo):
        return None

    try:
        escala = min(3.0, max(0.7, float(escala or 1.0)))
    except (TypeError, ValueError):
        escala = 1.0

    try:
        origem_imagem, buffer_temporario = _preparar_imagem_pdf(caminho_logo, remover_bordas_brancas=remover_bordas_brancas)
        leitor = ImageReader(origem_imagem)
        largura_img, altura_img = leitor.getSize()
        if not largura_img or not altura_img:
            raise ValueError('Imagem inválida')

        largura_alvo = float(largura_max) * escala
        altura_alvo = float(altura_max) * escala
        proporcao = min(largura_alvo / float(largura_img), altura_alvo / float(altura_img))
        largura_final = largura_img * proporcao
        altura_final = altura_img * proporcao

        logo = Image(origem_imagem, width=largura_final, height=altura_final)
        logo.hAlign = 'LEFT'
        if buffer_temporario is not None:
            logo._imagem_buffer = buffer_temporario
        return logo
    except Exception:
        logo = Image(caminho_logo, width=largura_max * escala, height=altura_max * escala)
        logo.hAlign = 'LEFT'
        return logo


@export_bp.route('/gerar-pdf/<int:id>')
def gerar_pdf_ordem(id):
    """Gera recibo profissional da ordem de serviço"""

    if not PDF_AVAILABLE:
        return jsonify({'erro': 'Biblioteca ReportLab não instalada'}), 500

    try:
        from models import Ordem, Cliente

        ordem = db.session.get(Ordem, id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404

        cliente = db.session.get(Cliente, ordem.cliente_id)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=10*mm,
            leftMargin=10*mm,
            topMargin=10*mm,
            bottomMargin=10*mm
        )
        largura_conteudo = doc.width

        elementos = []
        styles = getSampleStyleSheet()

        def larguras_proporcionais(largura_total, proporcoes):
            """Distribui a largura total mantendo as proporcoes informadas."""
            soma = float(sum(proporcoes))
            return [(largura_total * p) / soma for p in proporcoes]

        def moeda(valor):
            return f"R$ {float(valor or 0):.2f}".replace('.', ',')

        # Medidas visuais padronizadas (ajustadas para impressao)
        logo_size = 34 * mm
        qr_size = 24 * mm
        qr_gap = 4 * mm

        # ===== ESTILOS PERSONALIZADOS =====
        estilo_nome_empresa = ParagraphStyle(
            'NomeEmpresa',
            parent=styles['Normal'],
            fontSize=19,
            textColor=colors.HexColor('#0a3147'),
            fontName='Helvetica-Bold',
            alignment=0,
            leading=22,
            spaceAfter=4
        )

        estilo_dados_empresa = ParagraphStyle(
            'DadosEmpresa',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#444444'),
            alignment=0,
            leading=13
        )

        estilo_titulo_ordem = ParagraphStyle(
            'TituloOrdem',
            parent=styles['Normal'],
            fontSize=16,
            textColor=colors.HexColor('#c44536'),
            fontName='Helvetica-Bold',
            alignment=1,
            spaceAfter=8,
            spaceBefore=5
        )

        estilo_secao = ParagraphStyle(
            'Secao',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#0a3147'),
            fontName='Helvetica-Bold',
            spaceAfter=5,
            spaceBefore=8,
            leftIndent=0
        )

        estilo_normal = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            leading=14
        )

        estilo_label = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#0a3147'),
            fontName='Helvetica-Bold',
            leading=14
        )

        estilo_valor = ParagraphStyle(
            'Valor',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#27ae60'),
            fontName='Helvetica-Bold',
            alignment=2
        )

        estilo_total = ParagraphStyle(
            'Total',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#0a3147'),
            fontName='Helvetica-Bold',
            alignment=2
        )

        estilo_total_geral = ParagraphStyle(
            'TotalGeral',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#c44536'),
            fontName='Helvetica-Bold',
            alignment=2
        )

        estilo_assinatura = ParagraphStyle(
            'Assinatura',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            alignment=0,
            spaceBefore=0
        )

        # ===========================================
        # CABEÇALHO
        # ===========================================
        branding = _obter_branding_empresa()
        logo_path = branding.get('logo_path') or ''
        if logo_path and os.path.exists(logo_path):
            logo = _criar_logo_pdf(
                logo_path,
                logo_size,
                logo_size,
                branding.get('logo_escala', 1.0),
                remover_bordas_brancas=True,
            )
            logo_bloco = Table([[logo]], colWidths=[logo_size], hAlign='LEFT')
            logo_bloco.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), -3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
        else:
            logo_bloco = Paragraph("OF39", ParagraphStyle('Logo', fontSize=18))

        empresa_nome = Paragraph(branding['empresa_nome'], estilo_nome_empresa)
        empresa_dados = Paragraph(
            f"<b>Contato:</b> {branding['empresa_telefone']}<br/>"
            f"<b>E-mail:</b> {branding['empresa_email']}<br/>"
            f"<b>Endereço:</b> {branding['empresa_endereco']}",
            estilo_dados_empresa
        )
        empresa_bloco = Table([[empresa_nome], [empresa_dados]], hAlign='LEFT')
        empresa_bloco.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        qr_imagens = []
        for caminho_qr in [branding.get('qrcode_1_path') or '', branding.get('qrcode_2_path') or '']:
            if caminho_qr and os.path.exists(caminho_qr):
                qr_imagens.append(_criar_logo_pdf(caminho_qr, qr_size, qr_size))

        if qr_imagens:
            if len(qr_imagens) == 2:
                qr_tabela = Table([[qr_imagens[0], qr_imagens[1]]], colWidths=[qr_size, qr_size])
            else:
                qr_tabela = Table([[qr_imagens[0]]], colWidths=[qr_size])
            qr_tabela.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
        else:
            qr_tabela = Paragraph("", estilo_normal)

        qr_largura = (len(qr_imagens) * qr_size) + (max(0, len(qr_imagens) - 1) * qr_gap)
        qr_largura = qr_largura if qr_largura > 0 else 28 * mm
        logo_largura = logo_size + 2 * mm
        empresa_largura = max(70 * mm, largura_conteudo - logo_largura - qr_largura)

        cabecalho_tabela = Table(
            [[logo_bloco, empresa_bloco, qr_tabela]],
            colWidths=[logo_largura, empresa_largura, qr_largura],
            hAlign='LEFT'
        )
        cabecalho_tabela.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (1, 0), (1, -1), 4),
            ('LEFTPADDING', (2, 0), (2, -1), 6),
        ]))
        elementos.append(cabecalho_tabela)
        linha_cabecalho = Table([['']], colWidths=[largura_conteudo], hAlign='LEFT')
        linha_cabecalho.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#d9d9d9')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elementos.append(linha_cabecalho)
        elementos.append(Spacer(1, 2*mm))

        # ===========================================
        # TÍTULO
        # ===========================================
        elementos.append(
            Paragraph(f"ORDEM DE SERVIÇO #{ordem.id}", estilo_titulo_ordem))
        elementos.append(Spacer(1, 3*mm))

        # ===========================================
        # DADOS DO CLIENTE E VEÍCULO
        # ===========================================
        elementos.append(Spacer(1, 2*mm))

        dados_cliente = []

        # Cliente
        dados_cliente.append([
            Paragraph("Cliente:", estilo_label),
            Paragraph(cliente.nome_cliente or '---', estilo_normal)
        ])

        # CPF
        dados_cliente.append([
            Paragraph("CPF:", estilo_label),
            Paragraph(cliente.cpf or '---', estilo_normal)
        ])

        # Veículo
        veiculo_str = f"{cliente.fabricante or ''} {cliente.modelo or ''} - {cliente.placa or ''} - {cliente.ano or ''} {cliente.cor or ''}".strip()
        if veiculo_str and veiculo_str != '- - -':
            dados_cliente.append([
                Paragraph("Veículo:", estilo_label),
                Paragraph(veiculo_str, estilo_normal)
            ])

        # Profissional responsável
        dados_cliente.append([
            Paragraph("Profissional:", estilo_label),
            Paragraph(ordem.profissional_responsavel or '---', estilo_normal)
        ])

        if dados_cliente:
            dados_table = Table(
                dados_cliente,
                colWidths=larguras_proporcionais(largura_conteudo, [32, 158]),
                hAlign='LEFT'
            )
            dados_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fb')),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e5e7eb')),
            ]))
            elementos.append(dados_table)
            elementos.append(Spacer(1, 4*mm))

        # ===========================================
        # SERVIÇOS
        # ===========================================
        elementos.append(Paragraph("SERVICOS REALIZADOS", estilo_secao))

        if ordem.servicos and len(ordem.servicos) > 0:
            servicos_data = [['Código', 'Descrição', 'Valor']]
            for s in ordem.servicos:
                servicos_data.append([
                    s.codigo_servico or '---',
                    s.descricao_servico or '---',
                    moeda(s.valor_servico)
                ])

            servicos_table = Table(
                servicos_data,
                colWidths=larguras_proporcionais(largura_conteudo, [24, 116, 50]),
                hAlign='LEFT'
            )
            servicos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0a3147')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),

                # Cabeçalhos alinhados
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

                # Corpo da tabela
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elementos.append(servicos_table)
        else:
            elementos.append(
                Paragraph("Nenhum serviço registrado", estilo_normal))
        elementos.append(Spacer(1, 5*mm))

        # ===========================================
        # PEÇAS
        # ===========================================
        elementos.append(Paragraph("PECAS UTILIZADAS", estilo_secao))

        if ordem.pecas and len(ordem.pecas) > 0:
            pecas_data = [['Código', 'Descrição', 'Qtd', 'Lucro %', 'Valor Unit.', 'Total']]
            for p in ordem.pecas:
                total = p.quantidade * p.valor_unitario
                pecas_data.append([
                    p.codigo_peca or '---',
                    p.descricao_peca or '---',
                    str(p.quantidade),
                    f"{float(getattr(p, 'percentual_lucro', 0) or 0):.2f}%",
                    moeda(p.valor_unitario),
                    moeda(total)
                ])

            # Oculta o percentual de lucro no documento entregue ao cliente.
            pecas_data = [[linha[i] for i in (0, 1, 2, 4, 5)] for linha in pecas_data]

            pecas_table = Table(
                pecas_data,
                colWidths=larguras_proporcionais(largura_conteudo, [24, 92, 18, 28, 28]),
                hAlign='LEFT'
            )
            pecas_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0a3147')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),

                # Cabeçalhos alinhados
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

                # Corpo da tabela
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elementos.append(pecas_table)
        else:
            elementos.append(
                Paragraph("Nenhuma peça registrada", estilo_normal))
        elementos.append(Spacer(1, 8*mm))

        # ===========================================
        # RESUMO DE VALORES
        # ===========================================
        desconto_valor = float(getattr(ordem, 'desconto_valor', 0) or 0)
        total_pago = float(getattr(ordem, 'total_pago', 0) or 0)
        saldo_pendente = float(getattr(ordem, 'saldo_pendente', 0) or 0)
        total_final = float(getattr(ordem, 'total_cobrado', ordem.total_geral) or 0)

        resumo_data = [
            [Paragraph('Total Servicos:', estilo_normal),
             Paragraph(moeda(ordem.total_servicos), estilo_valor)],
            [Paragraph('Total Pecas:', estilo_normal),
             Paragraph(moeda(ordem.total_pecas), estilo_valor)],
        ]
        if desconto_valor > 0.009:
            resumo_data.append([
                Paragraph('Desconto aplicado:', estilo_normal),
                Paragraph(moeda(desconto_valor), estilo_valor)
            ])
        if total_pago > 0.009:
            resumo_data.append([
                Paragraph('Total pago:', estilo_normal),
                Paragraph(moeda(total_pago), estilo_valor)
            ])
        if saldo_pendente > 0.009:
            resumo_data.append([
                Paragraph('Saldo pendente:', estilo_normal),
                Paragraph(moeda(saldo_pendente), estilo_valor)
            ])
        resumo_data.append([
            Paragraph('TOTAL FINAL DA VENDA:', estilo_total_geral),
            Paragraph(moeda(total_final), estilo_total_geral)
        ])

        resumo_table = Table(
            resumo_data,
            colWidths=larguras_proporcionais(largura_conteudo, [140, 50]),
            hAlign='LEFT'
        )
        resumo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, 0), (1, 0), 0.5, colors.HexColor('#dddddd')),
            ('LINEABOVE', (0, -1), (1, -1), 0.75, colors.HexColor('#dddddd')),
            ('TOPPADDING', (0, 0), (1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (1, -1), 4),
            ('BACKGROUND', (0, 0), (1, -2), colors.HexColor('#f8f9fb')),
        ]))
        elementos.append(resumo_table)
        elementos.append(Spacer(1, 8*mm))

        pagamentos = getattr(ordem, 'pagamentos', []) or []
        if saldo_pendente > 0.009 or pagamentos:
            elementos.append(Paragraph("SITUAÇÃO FINANCEIRA", estilo_secao))

        if saldo_pendente > 0.009:
            detalhes_debito = []
            detalhes_debito.append(
                f"<b>Valor restante em aberto:</b> {moeda(saldo_pendente)}"
            )
            if getattr(ordem, 'debito_vencimento', None):
                detalhes_debito.append(
                    f"<b>Vencimento:</b> {ordem.debito_vencimento.strftime('%d/%m/%Y')}"
                )
            if getattr(ordem, 'debito_observacao', None):
                detalhes_debito.append(
                    f"<b>Observação do débito:</b> {ordem.debito_observacao}"
                )
            elementos.append(Paragraph('<br/>'.join(detalhes_debito), estilo_normal))
            elementos.append(Spacer(1, 3*mm))

        if pagamentos:
            pagamentos_data = [['Data', 'Forma', 'Valor', 'Observação']]
            for pg in pagamentos:
                pagamentos_data.append([
                    pg.data_pagamento.strftime('%d/%m/%Y %H:%M') if getattr(pg, 'data_pagamento', None) else '---',
                    pg.forma_pagamento or '---',
                    moeda(pg.valor),
                    pg.observacao or '---'
                ])

            pagamentos_table = Table(
                pagamentos_data,
                colWidths=larguras_proporcionais(largura_conteudo, [34, 30, 26, 100]),
                hAlign='LEFT'
            )
            pagamentos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0a3147')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elementos.append(pagamentos_table)
        else:
            elementos.append(Paragraph("Nenhum pagamento registrado", estilo_normal))
        elementos.append(Spacer(1, 8*mm))

        # ===========================================
        # ASSINATURA
        # ===========================================
        elementos.append(Paragraph("ASSINATURA DO CLIENTE", estilo_secao))
        elementos.append(Spacer(1, 6*mm))

        assinatura_linha = "__________________________________________________"
        if ordem.assinatura_cliente:
            elementos.append(
                Paragraph(ordem.assinatura_cliente, estilo_assinatura))
        else:
            elementos.append(Paragraph(assinatura_linha, estilo_assinatura))

        elementos.append(Spacer(1, 2*mm))
        elementos.append(Paragraph("(assinatura)", estilo_assinatura))
        elementos.append(Spacer(1, 5*mm))

        # ===========================================
        # RODAPÉ
        # ===========================================
        rodape_style = ParagraphStyle(
            'Rodape',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=1
        )
        elementos.append(Paragraph(
            f"Documento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", rodape_style))
        elementos.append(Paragraph("Obrigado pela preferência!", rodape_style))

        # Construir PDF
        doc.build(elementos)

        buffer.seek(0)
        visualizar_inline = (request.args.get('inline') or '').strip() in {'1', 'true', 'yes'}
        return send_file(
            buffer,
            as_attachment=not visualizar_inline,
            download_name=f'recibo_ordem_{id}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@export_bp.route('/fechamento-mensal-contador-pdf', methods=['GET'])
def gerar_pdf_fechamento_mensal_contador():
    """Gera PDF mensal com produção por profissional e resumo por forma de pagamento."""
    if not PDF_AVAILABLE:
        return jsonify({'erro': 'Biblioteca ReportLab não instalada'}), 500

    try:
        from sqlalchemy import func
        from models import Ordem, ItemServico

        mes = (request.args.get('mes') or '').strip()  # YYYY-MM
        if mes:
            data_base = datetime.strptime(f'{mes}-01', '%Y-%m-%d')
        else:
            hoje = datetime.now()
            data_base = datetime(hoje.year, hoje.month, 1)

        data_inicio = datetime(data_base.year, data_base.month, 1, 0, 0, 0, 0)
        if data_base.month == 12:
            prox = datetime(data_base.year + 1, 1, 1)
        else:
            prox = datetime(data_base.year, data_base.month + 1, 1)
        data_fim = prox - timedelta(microseconds=1)

        profissional_expr = func.coalesce(
            func.nullif(func.trim(ItemServico.nome_profissional), ''),
            func.nullif(func.trim(Ordem.profissional_responsavel), ''),
            'Nao informado'
        )
        data_ref_expr = func.coalesce(
            Ordem.data_conclusao,
            Ordem.data_retirada,
            Ordem.data_emissao,
            Ordem.data_entrada
        )

        ranking_rows = (
            ItemServico.query.join(Ordem, ItemServico.ordem_id == Ordem.id)
            .filter(data_ref_expr >= data_inicio, data_ref_expr <= data_fim)
            .with_entities(
                profissional_expr.label('profissional'),
                func.count(ItemServico.id).label('quantidade_servicos'),
                func.coalesce(func.sum(ItemServico.valor_servico), 0.0).label('valor_total'),
                func.coalesce(func.avg(ItemServico.valor_servico), 0.0).label('media_por_servico')
            )
            .group_by(profissional_expr)
            .order_by(func.coalesce(func.sum(ItemServico.valor_servico), 0.0).desc())
            .all()
        )

        pagamentos_rows = (
            Ordem.query
            .with_entities(
                func.coalesce(func.nullif(func.trim(Ordem.forma_pagamento), ''), 'Não informado').label('forma_pagamento'),
                func.coalesce(func.sum(Ordem.total_geral), 0.0).label('valor_total'),
                func.count(Ordem.id).label('quantidade')
            )
            .filter(Ordem.status.in_(['Concluído', 'Garantia']))
            .filter(Ordem.data_conclusao >= data_inicio, Ordem.data_conclusao <= data_fim)
            .group_by('forma_pagamento')
            .order_by(func.coalesce(func.sum(Ordem.total_geral), 0.0).desc())
            .all()
        )

        total_geral = float(sum(float(r.valor_total or 0) for r in ranking_rows))

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=12*mm, leftMargin=12*mm, topMargin=12*mm, bottomMargin=12*mm
        )
        elementos = []
        styles = getSampleStyleSheet()

        titulo = ParagraphStyle(
            'Titulo', parent=styles['Heading1'], fontName='Helvetica-Bold',
            fontSize=16, textColor=colors.HexColor('#0a3147'), alignment=1, spaceAfter=8
        )
        subt = ParagraphStyle(
            'Subt', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#666666'), alignment=1, spaceAfter=12
        )
        secao = ParagraphStyle(
            'Secao', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#0a3147'), spaceBefore=8, spaceAfter=6
        )

        elementos.append(Paragraph('Fechamento Mensal - Contador', titulo))
        elementos.append(Paragraph(f'Período: {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}', subt))
        elementos.append(Paragraph(f'Total geral do período: R$ {total_geral:.2f}'.replace('.', ','), styles['Normal']))
        elementos.append(Spacer(1, 4*mm))

        elementos.append(Paragraph('Produção por Profissional', secao))
        tabela_prof = [['Profissional', 'Qtd Serviços', 'Valor Total', 'Média']]
        for r in ranking_rows:
            tabela_prof.append([
                r.profissional,
                str(int(r.quantidade_servicos or 0)),
                f'R$ {float(r.valor_total or 0):.2f}'.replace('.', ','),
                f'R$ {float(r.media_por_servico or 0):.2f}'.replace('.', ',')
            ])
        if len(tabela_prof) == 1:
            tabela_prof.append(['Sem dados', '0', 'R$ 0,00', 'R$ 0,00'])

        tab1 = Table(tabela_prof, colWidths=[70*mm, 30*mm, 40*mm, 35*mm], hAlign='LEFT')
        tab1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0a3147')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7f7f7'))
        ]))
        elementos.append(tab1)
        elementos.append(Spacer(1, 6*mm))

        elementos.append(Paragraph('Resumo por Forma de Pagamento', secao))
        tabela_pag = [['Forma', 'Quantidade', 'Valor Total']]
        for p in pagamentos_rows:
            tabela_pag.append([
                p.forma_pagamento,
                str(int(p.quantidade or 0)),
                f'R$ {float(p.valor_total or 0):.2f}'.replace('.', ',')
            ])
        if len(tabela_pag) == 1:
            tabela_pag.append(['Sem dados', '0', 'R$ 0,00'])

        tab2 = Table(tabela_pag, colWidths=[90*mm, 30*mm, 55*mm], hAlign='LEFT')
        tab2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0a3147')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7f7f7'))
        ]))
        elementos.append(tab2)

        doc.build(elementos)
        buffer.seek(0)
        nome = f'fechamento_mensal_contador_{data_inicio.strftime("%Y_%m")}.pdf'
        return send_file(buffer, as_attachment=True, download_name=nome, mimetype='application/pdf')

    except ValueError:
        return jsonify({'erro': 'Formato inválido. Use mes=YYYY-MM.'}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@export_bp.route('/exportar', methods=['GET'])
def exportar_dados():
    """Exporta dados para db, csv, xlsx ou json."""
    try:
        tipo = (request.args.get('tipo') or 'completo').strip().lower()
        formato = (request.args.get('formato') or 'db').strip().lower()
        tipos_validos = {'completo', 'clientes', 'ordens', 'financeiro'}
        formatos_validos = {'db', 'csv', 'xlsx', 'json'}

        if tipo not in tipos_validos:
            return jsonify({'erro': 'Tipo de exportação inválido.'}), 400
        if formato not in formatos_validos:
            return jsonify({'erro': 'Formato de exportação inválido.'}), 400

        nome_arquivo = ExportService.get_nome_arquivo(tipo, formato)

        if formato == 'db':
            if tipo != 'completo':
                return jsonify({'erro': 'Exportação .db disponível apenas para tipo completo.'}), 400
            caminho_db = ExportService.get_database_path()
            if not os.path.exists(caminho_db):
                return jsonify({'erro': 'Arquivo database.db não encontrado.'}), 404
            return send_file(caminho_db, as_attachment=True, download_name=nome_arquivo, mimetype='application/octet-stream')

        if formato == 'csv':
            conteudo = ExportService.exportar_csv(tipo).getvalue()
            return Response(
                conteudo,
                mimetype='text/csv; charset=utf-8',
                headers={'Content-Disposition': f'attachment; filename={nome_arquivo}'}
            )

        if formato == 'xlsx':
            arquivo = ExportService.exportar_excel(tipo)
            return send_file(
                arquivo,
                as_attachment=True,
                download_name=nome_arquivo,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        dados = ExportService.exportar_json(tipo)
        return Response(
            json.dumps(dados, ensure_ascii=False, indent=2),
            mimetype='application/json; charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename={nome_arquivo}'}
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@export_bp.route('/importar', methods=['POST'])
def importar_dados():
    """Importa dados de json, csv ou xlsx."""
    try:
        import pandas as pd

        arquivo = request.files.get('arquivo')
        tipo = (request.form.get('tipo') or 'completo').strip().lower()
        formato = (request.form.get('formato') or '').strip().lower()

        if not arquivo:
            return jsonify({'erro': 'Arquivo não enviado.'}), 400
        if not formato:
            nome = (arquivo.filename or '').lower()
            if nome.endswith('.json'):
                formato = 'json'
            elif nome.endswith('.csv'):
                formato = 'csv'
            elif nome.endswith('.xlsx'):
                formato = 'xlsx'
        if formato not in {'json', 'csv', 'xlsx'}:
            return jsonify({'erro': 'Formato inválido para importação.'}), 400

        if formato in {'csv', 'xlsx'} and tipo == 'completo':
            return jsonify({'erro': 'Importação completa via CSV/XLSX não é suportada. Use JSON.'}), 400

        if formato == 'json':
            dados = json.load(arquivo.stream)
            resultados = ExportService.importar_json(dados, tipo)
        elif formato == 'csv':
            df = pd.read_csv(arquivo.stream, sep=None, engine='python')
            resultados = ExportService.importar_tabular(df, tipo)
        else:
            df = pd.read_excel(arquivo.stream)
            resultados = ExportService.importar_tabular(df, tipo)

        db.session.commit()
        return jsonify(resultados)

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

