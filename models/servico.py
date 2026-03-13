# ===========================================
# models/servico.py - Modelo de Item de Serviço
# ===========================================

from datetime import datetime  # ← ADICIONADO
from extensions import db

class ItemServico(db.Model):
    __tablename__ = 'servicos'
    
    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey('ordens.id'), nullable=False)
    codigo_servico = db.Column(db.String(20))
    descricao_servico = db.Column(db.String(200))
    nome_profissional = db.Column(db.String(120))
    valor_servico = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)  # ← ADICIONADO
    
    # ✅ RELACIONAMENTO CORRIGIDO (para consistência com back_populates)
    ordem = db.relationship('Ordem', back_populates='servicos')
    
    def to_dict(self):
        """Converte o objeto para dicionário (para JSON)"""
        return {
            'id': self.id,
            'ordem_id': self.ordem_id,
            'codigo_servico': self.codigo_servico,
            'descricao_servico': self.descricao_servico,
            'nome_profissional': self.nome_profissional,
            'valor_servico': self.valor_servico,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ItemServico {self.codigo_servico} - {self.descricao_servico[:30]}>'
