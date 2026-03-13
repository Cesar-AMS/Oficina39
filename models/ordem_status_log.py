# ===========================================
# models/ordem_status_log.py - Auditoria de Status da OS
# ===========================================

from datetime import datetime
from extensions import db


class OrdemStatusLog(db.Model):
    __tablename__ = 'ordem_status_logs'

    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey('ordens.id'), nullable=False, index=True)
    status_anterior = db.Column(db.String(50))
    status_novo = db.Column(db.String(50), nullable=False)
    forma_pagamento = db.Column(db.String(30))
    operador = db.Column(db.String(80), default='sistema')
    origem = db.Column(db.String(40), default='api')
    observacao = db.Column(db.String(255))
    data_evento = db.Column(db.DateTime, default=datetime.now, nullable=False)

    ordem = db.relationship('Ordem', back_populates='logs_status')

    def to_dict(self):
        return {
            'id': self.id,
            'ordem_id': self.ordem_id,
            'status_anterior': self.status_anterior,
            'status_novo': self.status_novo,
            'forma_pagamento': self.forma_pagamento,
            'operador': self.operador,
            'origem': self.origem,
            'observacao': self.observacao,
            'data_evento': self.data_evento.strftime('%d/%m/%Y %H:%M') if self.data_evento else None
        }
