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
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M') if self.updated_at else None,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }
    
    def to_dict_completo(self):
        """Converte com senha (apenas para uso interno)"""
        dados = self.to_dict()
        dados['senha_app'] = self.senha_app
        return dados
    
    def __repr__(self):
        return f'<ConfigContador {self.email_cliente}>'
