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
from services.order_pdf_service import (
    generate_order_pdf_bytes,
    pdf_available as order_pdf_available,
    suggested_order_pdf_name,
)

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

    if not order_pdf_available():
        return jsonify({'erro': 'Biblioteca ReportLab não instalada'}), 500

    try:
        pdf_bytes = generate_order_pdf_bytes(id)
        buffer = io.BytesIO(pdf_bytes)
        visualizar_inline = (request.args.get('inline') or '').strip() in {'1', 'true', 'yes'}
        return send_file(
            buffer,
            as_attachment=not visualizar_inline,
            download_name=suggested_order_pdf_name(id),
            mimetype='application/pdf'
        )

    except LookupError as e:
        return jsonify({'erro': str(e)}), 404
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

