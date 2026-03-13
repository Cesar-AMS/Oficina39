# ===========================================
# models/saida.py - Modelo de Saída (Fluxo de Caixa)
# ===========================================

from datetime import datetime
from extensions import db  # ← CORRIGIDO: importar do extensions, não criar novo db

class Saida(db.Model):
    __tablename__ = 'saidas'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.now)
    categoria = db.Column(db.String(50), default='Outros')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        """Converte o objeto para dicionário (para JSON)"""
        return {
            'id': self.id,
            'descricao': self.descricao,
            'valor': self.valor,
            'data': self.data.strftime('%d/%m/%Y') if self.data else None,
            'categoria': self.categoria,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Saida {self.descricao[:30]} - R$ {self.valor:.2f}>'