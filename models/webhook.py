from __future__ import annotations

from datetime import datetime

from extensions import db


class Webhook(db.Model):
    __tablename__ = 'webhooks'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    eventos_json = db.Column('eventos', db.JSON, nullable=False, default=list)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    tentativas = db.Column(db.Integer, default=3, nullable=False)
    timeout = db.Column(db.Integer, default=10, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    ultima_chamada = db.Column(db.DateTime, nullable=True)
    ultimo_status = db.Column(db.Integer, nullable=True)

    api_key = db.relationship('ApiKey', lazy='joined')

    @property
    def eventos(self):
        return list(self.eventos_json or [])

    @eventos.setter
    def eventos(self, valor):
        self.eventos_json = list(valor or [])

    def aceita_evento(self, evento: str) -> bool:
        evento_limpo = (evento or '').strip().lower()
        return evento_limpo in {(item or '').strip().lower() for item in self.eventos}

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'eventos': self.eventos,
            'api_key_id': self.api_key_id,
            'ativo': bool(self.ativo),
            'tentativas': int(self.tentativas or 0),
            'timeout': int(self.timeout or 0),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ultima_chamada': self.ultima_chamada.isoformat() if self.ultima_chamada else None,
            'ultimo_status': self.ultimo_status,
        }
