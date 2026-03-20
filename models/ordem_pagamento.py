# ===========================================
# models/ordem_pagamento.py - Pagamentos da Ordem
# ===========================================

from datetime import datetime

from extensions import db


class OrdemPagamento(db.Model):
    __tablename__ = 'ordem_pagamentos'

    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey('ordens.id'), nullable=False, index=True)
    valor = db.Column(db.Float, nullable=False, default=0)
    forma_pagamento = db.Column(db.String(30), nullable=False)
    observacao = db.Column(db.String(255))
    data_pagamento = db.Column(db.DateTime, default=datetime.now, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    ordem = db.relationship('Ordem', back_populates='pagamentos')

    def to_dict(self):
        return {
            'id': self.id,
            'ordem_id': self.ordem_id,
            'valor': float(self.valor or 0),
            'forma_pagamento': self.forma_pagamento,
            'observacao': self.observacao,
            'data_pagamento': self.data_pagamento.strftime('%d/%m/%Y %H:%M') if self.data_pagamento else None,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None,
        }

    def __repr__(self):
        return f'<OrdemPagamento ordem={self.ordem_id} valor={self.valor}>'
