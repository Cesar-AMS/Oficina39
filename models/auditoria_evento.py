from datetime import datetime
from extensions import db


class AuditoriaEvento(db.Model):
    __tablename__ = 'auditoria_eventos'

    id = db.Column(db.Integer, primary_key=True)
    acao = db.Column(db.String(80), nullable=False, index=True)
    entidade = db.Column(db.String(80), nullable=False, index=True)
    entidade_id = db.Column(db.Integer, index=True)
    valor_anterior = db.Column(db.String(120))
    valor_novo = db.Column(db.String(120))
    observacao = db.Column(db.String(255))
    operador = db.Column(db.String(80), default='sistema')
    origem = db.Column(db.String(40), default='api')
    data_evento = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)

    @property
    def entidade_tipo(self):
        return self.entidade

    @entidade_tipo.setter
    def entidade_tipo(self, valor):
        self.entidade = valor

    def to_dict(self):
        return {
            'id': self.id,
            'acao': self.acao,
            'entidade': self.entidade,
            'entidade_tipo': self.entidade,
            'entidade_id': self.entidade_id,
            'valor_anterior': self.valor_anterior,
            'valor_novo': self.valor_novo,
            'observacao': self.observacao,
            'operador': self.operador,
            'origem': self.origem,
            'data_evento': self.data_evento.strftime('%d/%m/%Y %H:%M') if self.data_evento else None
        }
