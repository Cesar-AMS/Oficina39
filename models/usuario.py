from __future__ import annotations

from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


PERFIS_USUARIO = ('admin', 'gerente', 'operador', 'visualizador')


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(200), nullable=False)
    perfil = db.Column(db.String(30), default='operador', nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    ultimo_acesso = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def definir_senha(self, senha: str):
        self.senha_hash = generate_password_hash((senha or '').strip())

    def verificar_senha(self, senha: str) -> bool:
        if not self.senha_hash:
            return False
        return check_password_hash(self.senha_hash, (senha or '').strip())

    def registrar_acesso(self):
        self.ultimo_acesso = datetime.now()

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'perfil': self.perfil,
            'ativo': bool(self.ativo),
            'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
