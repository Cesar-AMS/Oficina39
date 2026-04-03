# ===========================================
# models/peca.py - Modelo de Item de Peça
# ===========================================

from extensions import db
from datetime import datetime


class Peca(db.Model):
    __tablename__ = 'catalogo_pecas'
    __table_args__ = (
        db.Index('idx_catalogo_pecas_codigo', 'codigo'),
        db.Index('idx_catalogo_pecas_estoque', 'estoque_atual'),
        db.Index('idx_catalogo_pecas_categoria', 'categoria'),
    )

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(40), nullable=False, unique=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    categoria = db.Column(db.String(80))
    descricao = db.Column(db.String(255))
    estoque_atual = db.Column(db.Float, default=0)
    valor_custo = db.Column(db.Float, default=0)
    percentual_lucro = db.Column(db.Float, default=0)
    valor_unitario = db.Column(db.Float, default=0)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    deleted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def excluida(self):
        return bool(self.deleted_at) or not bool(self.ativo)

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'categoria': self.categoria,
            'descricao': self.descricao,
            'estoque_atual': float(self.estoque_atual or 0),
            'valor_custo': float(self.valor_custo or 0),
            'percentual_lucro': float(self.percentual_lucro or 0),
            'valor_unitario': float(self.valor_unitario or 0),
            'ativo': bool(self.ativo),
            'excluida': self.excluida,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Peca {self.codigo} - {self.nome}>'


class ItemPeca(db.Model):
    __tablename__ = 'pecas'
    
    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey('ordens.id'), nullable=False)
    codigo_peca = db.Column(db.String(20))
    descricao_peca = db.Column(db.String(200))
    quantidade = db.Column(db.Float, default=1)
    valor_custo = db.Column(db.Float, default=0)
    percentual_lucro = db.Column(db.Float, default=0)
    valor_unitario = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)  # ← ADICIONADO
    
    # ✅ RELACIONAMENTO CORRIGIDO (para consistência)
    ordem = db.relationship('Ordem', back_populates='pecas')
    
    @property
    def total(self):
        """Calcula o total da peça (quantidade * valor unitário)"""
        return float(self.quantidade or 0) * float(self.valor_unitario or 0)
    
    def to_dict(self):
        """Converte o objeto para dicionário (para JSON)"""
        return {
            'id': self.id,
            'ordem_id': self.ordem_id,
            'codigo_peca': self.codigo_peca,
            'descricao_peca': self.descricao_peca,
            'quantidade': self.quantidade,
            'valor_custo': self.valor_custo,
            'percentual_lucro': self.percentual_lucro,
            'valor_unitario': self.valor_unitario,
            'total': self.total,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ItemPeca {self.codigo_peca} - {self.descricao_peca[:30]}>'
