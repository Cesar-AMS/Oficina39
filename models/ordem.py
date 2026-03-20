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
    desconto_percentual = db.Column(db.Float, default=0)
    desconto_valor = db.Column(db.Float, default=0)
    debito_vencimento = db.Column(db.Date)
    debito_observacao = db.Column(db.String(255))
    total_servicos = db.Column(db.Float, default=0)
    total_pecas = db.Column(db.Float, default=0)
    total_geral = db.Column(db.Float, default=0)
    
    # ✅ RELACIONAMENTOS CORRIGIDOS (usando back_populates)
    cliente = db.relationship('Cliente', back_populates='ordens', foreign_keys=[cliente_id])
    servicos = db.relationship('ItemServico', back_populates='ordem', cascade='all, delete-orphan')
    pecas = db.relationship('ItemPeca', back_populates='ordem', cascade='all, delete-orphan')
    logs_status = db.relationship('OrdemStatusLog', back_populates='ordem', cascade='all, delete-orphan')
    anexos = db.relationship('OrdemAnexo', back_populates='ordem', cascade='all, delete-orphan')
    pagamentos = db.relationship('OrdemPagamento', back_populates='ordem', cascade='all, delete-orphan')
    
    def calcular_totais(self):
        """Calcula os totais da ordem baseado nos serviços e peças"""
        self.total_servicos = sum(s.valor_servico or 0 for s in self.servicos)
        self.total_pecas = sum(p.quantidade * p.valor_unitario for p in self.pecas)
        self.total_geral = self.total_servicos + self.total_pecas

    @property
    def total_pago(self):
        return sum(float(p.valor or 0) for p in self.pagamentos)

    @property
    def total_cobrado(self):
        total_bruto = float(self.total_geral or 0)
        desconto = float(self.desconto_valor or 0)
        return round(max(0, total_bruto - desconto), 2)

    @property
    def saldo_pendente(self):
        saldo = float(self.total_cobrado or 0) - float(self.total_pago or 0)
        return round(max(0, saldo), 2)

    @property
    def status_financeiro(self):
        total = float(self.total_cobrado or 0)
        pago = float(self.total_pago or 0)
        if total <= 0:
            return 'Sem valor'
        if pago <= 0:
            return 'Em aberto'
        if pago + 0.0001 < total:
            return 'Parcial'
        return 'Quitado'
    
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
            'desconto_percentual': float(self.desconto_percentual or 0),
            'desconto_valor': float(self.desconto_valor or 0),
            'debito_vencimento': self.debito_vencimento.strftime('%d/%m/%Y') if self.debito_vencimento else None,
            'debito_observacao': self.debito_observacao,
            'total_servicos': self.total_servicos,
            'total_pecas': self.total_pecas,
            'total_geral': self.total_geral,
            'total_cobrado': self.total_cobrado,
            'total_pago': self.total_pago,
            'saldo_pendente': self.saldo_pendente,
            'status_financeiro': self.status_financeiro,
            'servicos': [s.to_dict() for s in self.servicos],
            'pecas': [p.to_dict() for p in self.pecas],
            'pagamentos': [p.to_dict() for p in self.pagamentos],
            'anexos': [a.to_dict() for a in self.anexos]
        }
    
    def __repr__(self):
        return f'<Ordem #{self.id} - {self.status}>'
