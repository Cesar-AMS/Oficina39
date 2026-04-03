from datetime import datetime

from extensions import db


class StatusLog(db.Model):
    __tablename__ = 'status_logs'

    id = db.Column(db.Integer, primary_key=True)
    entidade_tipo = db.Column(db.String(50), nullable=False, index=True)
    entidade_id = db.Column(db.Integer, nullable=False, index=True)
    status_anterior = db.Column(db.String(50))
    status_novo = db.Column(db.String(50), nullable=False)
    motivo = db.Column(db.String(200))
    usuario_id = db.Column(db.Integer, nullable=True)
    metadata_json = db.Column('metadata', db.JSON, nullable=True)
    operador = db.Column(db.String(80), default='sistema')
    origem = db.Column(db.String(40), default='api')
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)

    def to_dict(self):
        dados_extras = dict(self.metadata_json or {})
        forma_pagamento = dados_extras.get('forma_pagamento')
        observacao = dados_extras.get('observacao') or self.motivo
        return {
            'id': self.id,
            'entidade_tipo': self.entidade_tipo,
            'entidade_id': self.entidade_id,
            'status_anterior': self.status_anterior,
            'status_novo': self.status_novo,
            'forma_pagamento': forma_pagamento,
            'operador': self.operador,
            'origem': self.origem,
            'observacao': observacao,
            'motivo': self.motivo,
            'usuario_id': self.usuario_id,
            'metadata': dados_extras,
            'data_evento': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None,
        }
