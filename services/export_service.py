# ===========================================
# services/export_service.py - Serviço de Exportação
# ===========================================

import csv
import json
import io
import pandas as pd
from models import Cliente, Ordem, Saida
from datetime import datetime

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
        """
        Importa dados de JSON
        
        Args:
            dados: Dicionário com dados a importar
            tipo: 'completo', 'clientes', 'ordens', 'financeiro'
        
        Returns:
            dict: Resultados da importação
        """
        from extensions import db
        
        resultados = {
            'clientes': 0,
            'ordens': 0,
            'saidas': 0
        }
        
        if 'clientes' in dados and tipo in ['completo', 'clientes']:
            for c in dados['clientes']:
                if 'id' in c:
                    del c['id']
                cliente = Cliente(**c)
                db.session.add(cliente)
                resultados['clientes'] += 1
        
        if 'ordens' in dados and tipo in ['completo', 'ordens']:
            for o in dados['ordens']:
                if 'id' in o:
                    del o['id']
                ordem = Ordem(**o)
                db.session.add(ordem)
                resultados['ordens'] += 1
        
        if 'saidas' in dados and tipo in ['completo', 'financeiro']:
            for s in dados['saidas']:
                if 'id' in s:
                    del s['id']
                saida = Saida(**s)
                db.session.add(saida)
                resultados['saidas'] += 1
        
        return resultados
    
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
