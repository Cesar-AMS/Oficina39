# ===========================================
# services/export_service.py - Serviço de Exportação
# ===========================================

import csv
import json
import io
import os
import pandas as pd
from datetime import datetime
from extensions import db
from models import Cliente, Ordem, Saida

class ExportService:
    """Serviço para exportação de dados em vários formatos"""

    @staticmethod
    def _excel_engine_disponivel():
        """Retorna engine disponível para escrita de XLSX."""
        try:
            import openpyxl  # noqa: F401
            return 'openpyxl'
        except Exception:
            pass
        try:
            import xlsxwriter  # noqa: F401
            return 'xlsxwriter'
        except Exception:
            return None
    
    @staticmethod
    def exportar_csv(tipo='completo'):
        """
        Exporta dados para CSV
        
        Args:
            tipo: 'completo', 'clientes', 'ordens', 'financeiro'
        
        Returns:
            StringIO: Conteúdo CSV
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        if tipo in ['completo', 'clientes']:
            ExportService._escrever_clientes_csv(writer)
        
        if tipo in ['completo', 'ordens']:
            if tipo == 'completo':
                writer.writerow([])
            ExportService._escrever_ordens_csv(writer)
        
        if tipo in ['completo', 'financeiro']:
            if tipo == 'completo':
                writer.writerow([])
            ExportService._escrever_saidas_csv(writer)
        
        output.seek(0)
        return output
    
    @staticmethod
    def _escrever_clientes_csv(writer):
        """Escreve dados de clientes no CSV"""
        writer.writerow(['ID', 'NOME', 'CPF', 'ENDERECO', 'PLACA', 'FABRICANTE', 
                        'MODELO', 'ANO', 'MOTOR', 'COMBUSTIVEL', 'COR', 'TANQUE', 'KM'])
        clientes = Cliente.query.all()
        for c in clientes:
            writer.writerow([
                c.id, c.nome_cliente, c.cpf, c.endereco, c.placa, c.fabricante,
                c.modelo, c.ano, c.motor, c.combustivel, c.cor, c.tanque, c.km
            ])
    
    @staticmethod
    def _escrever_ordens_csv(writer):
        """Escreve dados de ordens no CSV"""
        writer.writerow(['ID_OS', 'CLIENTE_ID', 'STATUS', 'DATA_ENTRADA', 
                        'TOTAL_SERVICOS', 'TOTAL_PECAS', 'TOTAL_GERAL'])
        ordens = Ordem.query.all()
        for o in ordens:
            writer.writerow([
                o.id, o.cliente_id, o.status, o.data_entrada,
                o.total_servicos, o.total_pecas, o.total_geral
            ])
    
    @staticmethod
    def _escrever_saidas_csv(writer):
        """Escreve dados de saídas no CSV"""
        writer.writerow(['ID_SAIDA', 'DATA', 'DESCRICAO', 'CATEGORIA', 'VALOR'])
        saidas = Saida.query.all()
        for s in saidas:
            writer.writerow([s.id, s.data, s.descricao, s.categoria, s.valor])
    
    @staticmethod
    def exportar_json(tipo='completo'):
        """
        Exporta dados para JSON
        
        Args:
            tipo: 'completo', 'clientes', 'ordens', 'financeiro'
        
        Returns:
            dict: Dados formatados para JSON
        """
        dados = {}
        
        if tipo in ['completo', 'clientes']:
            dados['clientes'] = [c.to_dict() for c in Cliente.query.all()]
        
        if tipo in ['completo', 'ordens']:
            dados['ordens'] = [o.to_dict() for o in Ordem.query.all()]
        
        if tipo in ['completo', 'financeiro']:
            dados['saidas'] = [s.to_dict() for s in Saida.query.all()]
        
        return dados
    
    @staticmethod
    def exportar_excel(tipo='completo'):
        """
        Exporta dados para Excel
        
        Args:
            tipo: 'completo', 'clientes', 'ordens', 'financeiro'
        
        Returns:
            BytesIO: Conteúdo do arquivo Excel
        """
        output = io.BytesIO()
        engine_excel = ExportService._excel_engine_disponivel()
        if not engine_excel:
            raise RuntimeError('Biblioteca para Excel não instalada. Instale openpyxl ou xlsxwriter.')
        
        with pd.ExcelWriter(output, engine=engine_excel) as writer:
            if tipo in ['completo', 'clientes']:
                ExportService._escrever_clientes_excel(writer)
            
            if tipo in ['completo', 'ordens']:
                ExportService._escrever_ordens_excel(writer)
            
            if tipo in ['completo', 'financeiro']:
                ExportService._escrever_saidas_excel(writer)
        
        output.seek(0)
        return output

    @staticmethod
    def get_database_path():
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        return os.path.join(base_dir, 'database.db')
    
    @staticmethod
    def _escrever_clientes_excel(writer):
        """Escreve dados de clientes no Excel"""
        dados_clientes = []
        for c in Cliente.query.all():
            dados_clientes.append({
                'ID': c.id,
                'NOME': c.nome_cliente,
                'CPF': c.cpf,
                'ENDERECO': c.endereco,
                'PLACA': c.placa,
                'FABRICANTE': c.fabricante,
                'MODELO': c.modelo,
                'ANO': c.ano,
                'MOTOR': c.motor,
                'COMBUSTIVEL': c.combustivel,
                'COR': c.cor,
                'TANQUE': c.tanque,
                'KM': c.km
            })
        df_clientes = pd.DataFrame(dados_clientes)
        df_clientes.to_excel(writer, sheet_name='Clientes', index=False)
    
    @staticmethod
    def _escrever_ordens_excel(writer):
        """Escreve dados de ordens no Excel"""
        dados_ordens = []
        for o in Ordem.query.all():
            dados_ordens.append({
                'ID_OS': o.id,
                'CLIENTE_ID': o.cliente_id,
                'STATUS': o.status,
                'DATA_ENTRADA': o.data_entrada,
                'TOTAL_SERVICOS': o.total_servicos,
                'TOTAL_PECAS': o.total_pecas,
                'TOTAL_GERAL': o.total_geral
            })
        df_ordens = pd.DataFrame(dados_ordens)
        df_ordens.to_excel(writer, sheet_name='Ordens', index=False)
    
    @staticmethod
    def _escrever_saidas_excel(writer):
        """Escreve dados de saídas no Excel"""
        dados_saidas = []
        for s in Saida.query.all():
            dados_saidas.append({
                'ID_SAIDA': s.id,
                'DATA': s.data,
                'DESCRICAO': s.descricao,
                'CATEGORIA': s.categoria,
                'VALOR': s.valor
            })
        df_saidas = pd.DataFrame(dados_saidas)
        df_saidas.to_excel(writer, sheet_name='Saidas', index=False)
    
    @staticmethod
    def importar_json(dados, tipo='completo'):
        from models import ItemPeca, ItemServico

        resultados = {'clientes': 0, 'ordens': 0, 'saidas': 0}

        if tipo in ('completo', 'clientes'):
            for c in dados.get('clientes', []):
                cpf = (c.get('cpf') or '').strip()
                if not cpf or Cliente.query.filter_by(cpf=cpf).first():
                    continue
                cliente = Cliente(
                    nome_cliente=(c.get('nome_cliente') or '').strip() or 'Sem nome',
                    cpf=cpf,
                    telefone=c.get('telefone') or '',
                    email=c.get('email') or '',
                    endereco=c.get('endereco') or '',
                    cidade=c.get('cidade') or '',
                    estado=c.get('estado') or '',
                    cep=c.get('cep') or '',
                    placa=c.get('placa') or '',
                    fabricante=c.get('fabricante') or '',
                    modelo=c.get('modelo') or '',
                    ano=c.get('ano') or '',
                    motor=c.get('motor') or '',
                    combustivel=c.get('combustivel') or '',
                    cor=c.get('cor') or '',
                    tanque=c.get('tanque') or '',
                    km=ExportService._to_int(c.get('km'), 0),
                    direcao=c.get('direcao') or '',
                    ar=c.get('ar') or ''
                )
                db.session.add(cliente)
                resultados['clientes'] += 1

        if tipo in ('completo', 'ordens'):
            for o in dados.get('ordens', []):
                cliente_id = o.get('cliente_id')
                if not cliente_id:
                    continue
                ordem = Ordem(
                    cliente_id=cliente_id,
                    diagnostico=o.get('diagnostico') or '',
                    observacao_interna=o.get('observacao_interna') or '',
                    profissional_responsavel=(o.get('profissional_responsavel') or '').strip(),
                    assinatura_cliente=o.get('assinatura_cliente') or '',
                    status=o.get('status') or 'Aguardando',
                    forma_pagamento=o.get('forma_pagamento') or None,
                    data_entrada=ExportService._parse_datetime(o.get('data_entrada')) or datetime.now(),
                    data_emissao=ExportService._parse_datetime(o.get('data_emissao')) or datetime.now(),
                    data_retirada=ExportService._parse_datetime(o.get('data_retirada')),
                    data_conclusao=ExportService._parse_datetime(o.get('data_conclusao')),
                    total_servicos=ExportService._to_float(o.get('total_servicos'), 0),
                    total_pecas=ExportService._to_float(o.get('total_pecas'), 0),
                    total_geral=ExportService._to_float(o.get('total_geral'), 0),
                )
                db.session.add(ordem)
                db.session.flush()

                for s in o.get('servicos', []):
                    db.session.add(ItemServico(
                        ordem_id=ordem.id,
                        codigo_servico=s.get('codigo_servico') or '',
                        descricao_servico=s.get('descricao_servico') or '',
                        nome_profissional=(s.get('nome_profissional') or ordem.profissional_responsavel or '').strip(),
                        valor_servico=ExportService._to_float(s.get('valor_servico'), 0),
                    ))

                for p in o.get('pecas', []):
                    db.session.add(ItemPeca(
                        ordem_id=ordem.id,
                        codigo_peca=p.get('codigo_peca') or '',
                        descricao_peca=p.get('descricao_peca') or '',
                        quantidade=ExportService._to_float(p.get('quantidade'), 0),
                        valor_unitario=ExportService._to_float(p.get('valor_unitario'), 0),
                    ))
                resultados['ordens'] += 1

        if tipo in ('completo', 'financeiro', 'saidas'):
            for s in dados.get('saidas', []):
                descricao = (s.get('descricao') or '').strip()
                if not descricao:
                    continue
                db.session.add(Saida(
                    descricao=descricao,
                    valor=ExportService._to_float(s.get('valor'), 0),
                    categoria=s.get('categoria') or 'Outros',
                    data=ExportService._parse_datetime(s.get('data')) or datetime.now()
                ))
                resultados['saidas'] += 1

        return resultados

    @staticmethod
    def importar_tabular(df, tipo):
        resultados = {'clientes': 0, 'ordens': 0, 'saidas': 0}
        linhas = ExportService._normalizar_linhas(df)

        if tipo == 'clientes':
            for r in linhas:
                cpf = str(r.get('cpf') or '').strip()
                if not cpf or Cliente.query.filter_by(cpf=cpf).first():
                    continue
                db.session.add(Cliente(
                    nome_cliente=str(r.get('nome') or r.get('nome_cliente') or '').strip() or 'Sem nome',
                    cpf=cpf,
                    endereco=str(r.get('endereco') or '').strip(),
                    placa=str(r.get('placa') or '').strip(),
                    fabricante=str(r.get('fabricante') or '').strip(),
                    modelo=str(r.get('modelo') or '').strip(),
                    ano=str(r.get('ano') or '').strip(),
                    motor=str(r.get('motor') or '').strip(),
                    combustivel=str(r.get('combustivel') or '').strip(),
                    cor=str(r.get('cor') or '').strip(),
                    tanque=str(r.get('tanque') or '').strip(),
                    km=ExportService._to_int(r.get('km'), 0)
                ))
                resultados['clientes'] += 1

        elif tipo == 'ordens':
            for r in linhas:
                cliente_id = ExportService._to_int(r.get('cliente_id'), 0)
                if not cliente_id:
                    continue
                db.session.add(Ordem(
                    cliente_id=cliente_id,
                    status=str(r.get('status') or 'Aguardando').strip() or 'Aguardando',
                    data_entrada=ExportService._parse_datetime(r.get('data_entrada')) or datetime.now(),
                    total_servicos=ExportService._to_float(r.get('total_servicos'), 0),
                    total_pecas=ExportService._to_float(r.get('total_pecas'), 0),
                    total_geral=ExportService._to_float(r.get('total_geral'), 0),
                ))
                resultados['ordens'] += 1

        elif tipo in ('financeiro', 'saidas'):
            for r in linhas:
                descricao = str(r.get('descricao') or '').strip()
                if not descricao:
                    continue
                db.session.add(Saida(
                    descricao=descricao,
                    valor=ExportService._to_float(r.get('valor'), 0),
                    categoria=str(r.get('categoria') or 'Outros').strip() or 'Outros',
                    data=ExportService._parse_datetime(r.get('data')) or datetime.now()
                ))
                resultados['saidas'] += 1

        return resultados

    @staticmethod
    def _parse_datetime(valor):
        if valor in (None, ''):
            return None
        if isinstance(valor, datetime):
            return valor
        texto = str(valor).strip()
        formatos = [
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(texto, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _to_float(valor, default=0.0):
        try:
            if valor in (None, ''):
                return float(default)
            return float(str(valor).replace(',', '.'))
        except Exception:
            return float(default)

    @staticmethod
    def _to_int(valor, default=0):
        try:
            if valor in (None, ''):
                return int(default)
            return int(float(valor))
        except Exception:
            return int(default)

    @staticmethod
    def _normalizar_linhas(df):
        df = df.fillna('')
        linhas = []
        for row in df.to_dict(orient='records'):
            linhas.append({str(k).strip().lower(): v for k, v in row.items()})
        return linhas
    
    @staticmethod
    def get_nome_arquivo(tipo, formato):
        """
        Gera nome do arquivo para download
        
        Args:
            tipo: Tipo de exportação
            formato: Formato do arquivo
        
        Returns:
            str: Nome do arquivo
        """
        data = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"exportacao_{tipo}_{data}.{formato}"
