# ===========================================
# routes/export_routes.py - Recibo Profissional
# ===========================================

import traceback
import json
from flask import Blueprint, jsonify, send_file, request, Response
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
    PDF_AVAILABLE = True
except ImportError as e:
    PDF_AVAILABLE = False
    print(f"ReportLab nao instalado. Erro: {e}")
    print("Para instalar: pip install reportlab")

export_bp = Blueprint('export', __name__, url_prefix='/api/export')


@export_bp.route('/gerar-pdf/<int:id>')
def gerar_pdf_ordem(id):
    """Gera recibo profissional da ordem de serviço"""

    if not PDF_AVAILABLE:
        return jsonify({'erro': 'Biblioteca ReportLab não instalada'}), 500

    try:
        from models import Ordem, Cliente

        ordem = Ordem.query.get(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404

        cliente = Cliente.query.get(ordem.cliente_id)

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
        logo_size = 42 * mm
        qr_size = 28 * mm
        qr_gap = 8 * mm

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
            leading=14
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
        cabecalho_linha1 = []

        # LOGO
        logo_path = os.path.join('static', 'images', 'picapau4.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=logo_size, height=logo_size)
            logo.hAlign = 'LEFT'
            logo_bloco = Table([[logo]], colWidths=[logo_size], hAlign='LEFT')
            logo_bloco.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), -22),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            cabecalho_linha1.append(logo_bloco)
        else:
            cabecalho_linha1.append(
                Paragraph("🚗", ParagraphStyle('Logo', fontSize=30)))

        # DADOS DA EMPRESA (bloco com hierarquia visual mais profissional)
        empresa_nome = Paragraph("OFICINA 39", estilo_nome_empresa)
        empresa_dados = Paragraph(
            "<b>Contato:</b> (11) 99209-2341<br/>"
            "<b>E-mail:</b> oficina39ca@gmail.com<br/>"
            "<b>Endereço:</b> Rua Noel Rosa, 39 - Poá - SP",
            estilo_dados_empresa
        )
        empresa_bloco = Table(
            [[empresa_nome], [empresa_dados]],
            colWidths=[90 * mm],
            hAlign='LEFT'
        )
        empresa_bloco.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        cabecalho_linha1.append(empresa_bloco)

        # QR CODES
        qr_imagens = []
        qr_insta_path = os.path.join(
            'static', 'images', 'qrcodeinstagram.jpeg')
        qr_whats_path = os.path.join('static', 'images', 'qrcodewhatsapp.jpeg')

        if os.path.exists(qr_insta_path):
            qr_insta = Image(qr_insta_path, width=qr_size, height=qr_size)
            qr_imagens.append(qr_insta)

        if os.path.exists(qr_whats_path):
            qr_whats = Image(qr_whats_path, width=qr_size, height=qr_size)
            qr_imagens.append(qr_whats)

        if qr_imagens:
            if len(qr_imagens) == 2:
                qr_tabela = Table(
                    [[qr_imagens[0], '', qr_imagens[1]]],
                    colWidths=[qr_size, qr_gap, qr_size]
                )
            else:
                qr_tabela = Table([[qr_imagens[0]]], colWidths=[qr_size])

            qr_tabela.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            cabecalho_linha1.append(qr_tabela)
        else:
            cabecalho_linha1.append(Paragraph("", estilo_normal))

        # TABELA PRINCIPAL DO CABEÇALHO
        cabecalho_tabela = Table(
            [cabecalho_linha1],
            colWidths=larguras_proporcionais(largura_conteudo, [44, 102, 64]),
            hAlign='LEFT'
        )
        cabecalho_tabela.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (0, -1), 0),
            ('LEFTPADDING', (1, 0), (1, -1), 0),
            # Logo ancorado no canto superior esquerdo da seção
            ('LEFTPADDING', (0, 0), (0, -1), -6),
            ('TOPPADDING', (0, 0), (0, -1), 0),
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
                Paragraph("Veiculo:", estilo_label),
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
        # SERVIÇOS - VERSÃO ENCOSTADA NOS CANTOS
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
        # PEÇAS - VERSÃO ENCOSTADA NOS CANTOS
        # ===========================================
        elementos.append(Paragraph("PECAS UTILIZADAS", estilo_secao))

        if ordem.pecas and len(ordem.pecas) > 0:
            pecas_data = [['Código', 'Descrição', 'Qtd', 'Valor Unit.', 'Total']]
            for p in ordem.pecas:
                total = p.quantidade * p.valor_unitario
                pecas_data.append([
                    p.codigo_peca or '---',
                    p.descricao_peca or '---',
                    str(p.quantidade),
                    moeda(p.valor_unitario),
                    moeda(total)
                ])

            pecas_table = Table(
                pecas_data,
                colWidths=larguras_proporcionais(largura_conteudo, [24, 78, 18, 35, 35]),
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
        resumo_data = [
            ['', ''],
            [Paragraph('Total Serviços:', estilo_normal),
             Paragraph(moeda(ordem.total_servicos), estilo_valor)],
            [Paragraph('Total Peças:', estilo_normal),
             Paragraph(moeda(ordem.total_pecas), estilo_valor)],
            [Paragraph('TOTAL GERAL:', estilo_total_geral),
             Paragraph(moeda(ordem.total_geral), estilo_total_geral)]
        ]

        resumo_table = Table(
            resumo_data,
            colWidths=larguras_proporcionais(largura_conteudo, [140, 50]),
            hAlign='LEFT'
        )
        resumo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, 2), (1, 2), 0.5, colors.HexColor('#dddddd')),
            ('LINEABOVE', (0, 3), (1, 3), 0.5, colors.HexColor('#dddddd')),
            ('TOPPADDING', (0, 2), (1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (1, -1), 3),
            ('BACKGROUND', (0, 1), (1, -1), colors.HexColor('#f8f9fb')),
        ]))
        elementos.append(resumo_table)
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
        return send_file(
            buffer,
            as_attachment=True,
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
