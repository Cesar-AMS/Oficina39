# ===========================================
# models/profissional.py - Cadastro de Profissionais
# ===========================================

from datetime import datetime
from extensions import db


class Profissional(db.Model):
    __tablename__ = 'profissionais'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    cnpj = db.Column(db.String(18), nullable=False, unique=True)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cnpj': self.cnpj,
            'ativo': self.ativo,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }

    def __repr__(self):
        return f'<Profissional {self.nome}>'
