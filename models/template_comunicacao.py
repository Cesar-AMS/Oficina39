from __future__ import annotations

from datetime import datetime

from extensions import db


class TemplateComunicacao(db.Model):
    __tablename__ = 'templates_comunicacao'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    canal = db.Column(db.String(20), nullable=False)
    assunto = db.Column(db.String(200), nullable=True)
    corpo = db.Column(db.Text, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'canal': self.canal,
            'assunto': self.assunto,
            'corpo': self.corpo,
            'ativo': bool(self.ativo),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
