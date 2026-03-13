# ===========================================
# models/envio.py - Modelo de Histórico de Envios
# ===========================================

from datetime import datetime
from extensions import db

class EnvioRelatorio(db.Model):
    __tablename__ = 'envios_relatorio'
    
    id = db.Column(db.Integer, primary_key=True)
    periodo = db.Column(db.String(50))  # diario, semanal, mensal
    formato = db.Column(db.String(20))  # html, csv, xlsx, pdf
    remetente = db.Column(db.String(100))
    destinatario = db.Column(db.String(100))
    status = db.Column(db.String(20))  # enviado, erro
    erro_msg = db.Column(db.Text, nullable=True)
    data_envio = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'periodo': self.periodo,
            'formato': self.formato,
            'remetente': self.remetente,
            'destinatario': self.destinatario,
            'status': self.status,
            'erro_msg': self.erro_msg,
            'data_envio': self.data_envio.strftime('%d/%m/%Y %H:%M') if self.data_envio else None
        }
    
    def __repr__(self):
        return f'<EnvioRelatorio {self.id} - {self.status}>'