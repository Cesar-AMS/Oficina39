# ===========================================
# models/peca.py - Modelo de Item de Peça
# ===========================================

from extensions import db
from datetime import datetime

class ItemPeca(db.Model):
    __tablename__ = 'pecas'
    
    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey('ordens.id'), nullable=False)
    codigo_peca = db.Column(db.String(20))
    descricao_peca = db.Column(db.String(200))
    quantidade = db.Column(db.Float, default=1)
    valor_unitario = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)  # ← ADICIONADO
    
    # ✅ RELACIONAMENTO CORRIGIDO (para consistência)
    ordem = db.relationship('Ordem', back_populates='pecas')
    
    @property
    def total(self):
        """Calcula o total da peça (quantidade * valor unitário)"""
        return self.quantidade * self.valor_unitario
    
    def to_dict(self):
        """Converte o objeto para dicionário (para JSON)"""
        return {
            'id': self.id,
            'ordem_id': self.ordem_id,
            'codigo_peca': self.codigo_peca,
            'descricao_peca': self.descricao_peca,
            'quantidade': self.quantidade,
            'valor_unitario': self.valor_unitario,
            'total': self.total,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ItemPeca {self.codigo_peca} - {self.descricao_peca[:30]}>'