from __future__ import annotations

from datetime import datetime

from extensions import db


CANAIS_COMUNICACAO = ('email', 'whatsapp', 'sms')
STATUS_COMUNICACAO = ('pendente', 'enviado', 'falhou')


class Comunicacao(db.Model):
    __tablename__ = 'comunicacoes'

    id = db.Column(db.Integer, primary_key=True)
    canal = db.Column(db.String(20), nullable=False)
    destino = db.Column(db.String(100), nullable=False)
    assunto = db.Column(db.String(200), nullable=True)
    mensagem = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pendente', nullable=False)
    erro = db.Column(db.String(500), nullable=True)
    entidade_tipo = db.Column(db.String(50), nullable=True)
    entidade_id = db.Column(db.Integer, nullable=True)
    enviado_em = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    metadata_json = db.Column('metadata', db.JSON, nullable=True)

    @property
    def metadata_extra(self):
        return self.metadata_json or {}

    @metadata_extra.setter
    def metadata_extra(self, valor):
        self.metadata_json = dict(valor or {})

    def to_dict(self):
        return {
            'id': self.id,
            'canal': self.canal,
            'destino': self.destino,
            'assunto': self.assunto,
            'mensagem': self.mensagem,
            'status': self.status,
            'erro': self.erro,
            'entidade_tipo': self.entidade_tipo,
            'entidade_id': self.entidade_id,
            'enviado_em': self.enviado_em.isoformat() if self.enviado_em else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.metadata_extra,
        }
