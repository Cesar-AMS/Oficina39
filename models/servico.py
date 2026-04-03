# ===========================================
# models/servico.py - Modelo de Item de Serviço
# ===========================================

from datetime import datetime  # ← ADICIONADO
from extensions import db


class Servico(db.Model):
    __tablename__ = 'catalogo_servicos'
    __table_args__ = (
        db.Index('idx_catalogo_servicos_nome', 'nome'),
        db.Index('idx_catalogo_servicos_categoria', 'categoria'),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    categoria = db.Column(db.String(80))
    descricao = db.Column(db.String(255))
    valor_padrao = db.Column(db.Float, default=0)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    deleted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def excluido(self):
        return bool(self.deleted_at) or not bool(self.ativo)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'categoria': self.categoria,
            'descricao': self.descricao,
            'valor_padrao': float(self.valor_padrao or 0),
            'ativo': bool(self.ativo),
            'excluido': self.excluido,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Servico {self.nome}>'

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
