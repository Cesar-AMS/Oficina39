# ===========================================
# models/config.py - Modelo de Configuração do Contador
# ===========================================

from datetime import datetime
from extensions import db  # ← CORRIGIDO: importar do extensions, não criar novo db

class ConfigContador(db.Model):
    __tablename__ = 'config_contador'
    
    id = db.Column(db.Integer, primary_key=True)
    email_cliente = db.Column(db.String(100))
    senha_app = db.Column(db.String(50))  # Senha de app do Gmail
    email_contador = db.Column(db.String(100))
    profissional_envio_auto = db.Column(db.String(120))
    frequencia = db.Column(db.String(20), default='diario')  # diario, semanal, mensal
    dia_envio = db.Column(db.Integer, default=1)  # Dia do mês para envio mensal
    ativo = db.Column(db.Boolean, default=True)
    cep_provider_ativo = db.Column(db.String(60))
    cep_provider_primario = db.Column(db.String(60))
    cep_api_key_primaria = db.Column(db.String(255))
    cep_provider_secundario = db.Column(db.String(60))
    cep_api_key_secundaria = db.Column(db.String(255))
    placa_provider_ativo = db.Column(db.String(60))
    placa_provider_primario = db.Column(db.String(60))
    placa_api_key_primaria = db.Column(db.String(255))
    placa_provider_secundario = db.Column(db.String(60))
    placa_api_key_secundaria = db.Column(db.String(255))
    whatsapp_orcamento = db.Column(db.String(30))
    nome_exibicao_sistema = db.Column(db.String(120))
    empresa_nome = db.Column(db.String(120))
    empresa_email = db.Column(db.String(120))
    empresa_telefone = db.Column(db.String(30))
    empresa_endereco = db.Column(db.String(180))
    logo_index_path = db.Column(db.String(255))
    logo_index_formato = db.Column(db.String(20), default='circulo')
    qrcode_1_path = db.Column(db.String(255))
    qrcode_2_path = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)  # ← ADICIONADO para consistência
    
    def to_dict(self):
        """Converte o objeto para dicionário (para JSON) - SEM a senha por segurança"""
        return {
            'id': self.id,
            'email_cliente': self.email_cliente,
            'email_contador': self.email_contador,
            'profissional_envio_auto': self.profissional_envio_auto,
            'frequencia': self.frequencia,
            'dia_envio': self.dia_envio,
            'ativo': self.ativo,
            'cep_provider_ativo': self.cep_provider_ativo,
            'cep_provider_primario': self.cep_provider_primario,
            'cep_provider_secundario': self.cep_provider_secundario,
            'placa_provider_ativo': self.placa_provider_ativo,
            'placa_provider_primario': self.placa_provider_primario,
            'placa_provider_secundario': self.placa_provider_secundario,
            'whatsapp_orcamento': self.whatsapp_orcamento,
            'nome_exibicao_sistema': self.nome_exibicao_sistema,
            'empresa_nome': self.empresa_nome,
            'empresa_email': self.empresa_email,
            'empresa_telefone': self.empresa_telefone,
            'empresa_endereco': self.empresa_endereco,
            'logo_index_path': self.logo_index_path,
            'logo_index_formato': self.logo_index_formato or 'circulo',
            'qrcode_1_path': self.qrcode_1_path,
            'qrcode_2_path': self.qrcode_2_path,
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M') if self.updated_at else None,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }
    
    def to_dict_completo(self):
        """Converte com senha (apenas para uso interno)"""
        dados = self.to_dict()
        dados['senha_app'] = self.senha_app
        dados['cep_api_key_primaria'] = self.cep_api_key_primaria
        dados['cep_api_key_secundaria'] = self.cep_api_key_secundaria
        dados['placa_api_key_primaria'] = self.placa_api_key_primaria
        dados['placa_api_key_secundaria'] = self.placa_api_key_secundaria
        return dados
    
    def __repr__(self):
        return f'<ConfigContador {self.email_cliente}>'
