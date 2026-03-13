# ===========================================
# models/ordem.py - Modelo de Ordem de Serviço
# ===========================================

from datetime import datetime
from extensions import db

class Ordem(db.Model):
    __tablename__ = 'ordens'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    diagnostico = db.Column(db.Text)
    observacao_interna = db.Column(db.Text)
    profissional_responsavel = db.Column(db.String(120))
    assinatura_cliente = db.Column(db.String(200))
    status = db.Column(db.String(50), default='Aguardando')
    forma_pagamento = db.Column(db.String(30))
    data_entrada = db.Column(db.DateTime, default=datetime.now)
    data_emissao = db.Column(db.DateTime, default=datetime.now)
    data_retirada = db.Column(db.DateTime)
    data_conclusao = db.Column(db.DateTime)
    total_servicos = db.Column(db.Float, default=0)
    total_pecas = db.Column(db.Float, default=0)
    total_geral = db.Column(db.Float, default=0)
    
    # ✅ RELACIONAMENTOS CORRIGIDOS (usando back_populates)
    cliente = db.relationship('Cliente', back_populates='ordens', foreign_keys=[cliente_id])
    servicos = db.relationship('ItemServico', back_populates='ordem', cascade='all, delete-orphan')
    pecas = db.relationship('ItemPeca', back_populates='ordem', cascade='all, delete-orphan')
    logs_status = db.relationship('OrdemStatusLog', back_populates='ordem', cascade='all, delete-orphan')
    anexos = db.relationship('OrdemAnexo', back_populates='ordem', cascade='all, delete-orphan')
    
    def calcular_totais(self):
        """Calcula os totais da ordem baseado nos serviços e peças"""
        self.total_servicos = sum(s.valor_servico or 0 for s in self.servicos)
        self.total_pecas = sum(p.quantidade * p.valor_unitario for p in self.pecas)
        self.total_geral = self.total_servicos + self.total_pecas
    
    def to_dict(self):
        """Converte o objeto para dicionário (para JSON)"""
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'cliente_nome': self.cliente.nome_cliente if self.cliente else None,
            'diagnostico': self.diagnostico,
            'observacao_interna': self.observacao_interna,
            'profissional_responsavel': self.profissional_responsavel,
            'assinatura_cliente': self.assinatura_cliente,
            'status': self.status,
            'forma_pagamento': self.forma_pagamento,
            'data_entrada': self.data_entrada.strftime('%d/%m/%Y %H:%M') if self.data_entrada else None,
            'data_emissao': self.data_emissao.strftime('%d/%m/%Y %H:%M') if self.data_emissao else None,
            'data_retirada': self.data_retirada.strftime('%d/%m/%Y %H:%M') if self.data_retirada else None,
            'data_conclusao': self.data_conclusao.strftime('%d/%m/%Y %H:%M') if self.data_conclusao else None,
            'total_servicos': self.total_servicos,
            'total_pecas': self.total_pecas,
            'total_geral': self.total_geral,
            'servicos': [s.to_dict() for s in self.servicos],
            'pecas': [p.to_dict() for p in self.pecas],
            'anexos': [a.to_dict() for a in self.anexos]
        }
    
    def __repr__(self):
        return f'<Ordem #{self.id} - {self.status}>'
