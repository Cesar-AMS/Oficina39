from datetime import datetime

from extensions import db


TIPOS_MOVIMENTO_CAIXA = {'entrada', 'saida'}
CATEGORIAS_MOVIMENTO_CAIXA = {'pagamento_os', 'despesa', 'retirada', 'credito'}
FORMAS_MOVIMENTO_CAIXA = {'dinheiro', 'pix', 'cartao', 'debito_conta'}


class MovimentoCaixa(db.Model):
    __tablename__ = 'movimentos_caixa'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False, index=True)
    categoria = db.Column(db.String(50), nullable=False, index=True)
    valor = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    data_movimento = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey('ordens.id'), nullable=True, index=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True, index=True)
    descricao = db.Column(db.String(200))
    forma_pagamento = db.Column(db.String(30), index=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    ordem = db.relationship('Ordem', backref=db.backref('movimentos_caixa', lazy='dynamic'))
    cliente = db.relationship('Cliente', backref=db.backref('movimentos_caixa', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'valor': float(self.valor or 0),
            'data_movimento': self.data_movimento.strftime('%d/%m/%Y %H:%M') if self.data_movimento else None,
            'ordem_id': self.ordem_id,
            'cliente_id': self.cliente_id,
            'descricao': self.descricao,
            'forma_pagamento': self.forma_pagamento,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None,
        }

    def __repr__(self):
        return f'<MovimentoCaixa {self.tipo} {self.categoria} valor={float(self.valor or 0):.2f}>'
