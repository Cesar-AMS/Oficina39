from __future__ import annotations

from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class ApiKey(db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    key = db.Column(db.String(64), unique=True, nullable=False)
    secret_hash = db.Column(db.String(200), nullable=True)
    secret_token = db.Column(db.Text, nullable=True)
    permissoes_json = db.Column('permissoes', db.JSON, default=list, nullable=False)
    rate_limit = db.Column(db.Integer, default=100, nullable=False)
    ativa = db.Column(db.Boolean, default=True, nullable=False)
    ultimo_uso = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    expira_em = db.Column(db.DateTime, nullable=True)

    @property
    def permissoes(self):
        return list(self.permissoes_json or [])

    @permissoes.setter
    def permissoes(self, valor):
        self.permissoes_json = list(valor or [])

    def definir_secret(self, secret: str):
        self.secret_hash = generate_password_hash((secret or '').strip())

    def verificar_secret(self, secret: str) -> bool:
        if not self.secret_hash:
            return False
        return check_password_hash(self.secret_hash, (secret or '').strip())

    def registrar_uso(self):
        self.ultimo_uso = datetime.now()

    def expirada(self) -> bool:
        return bool(self.expira_em and self.expira_em <= datetime.now())

    def possui_permissao(self, permissao: str) -> bool:
        permissao_limpa = (permissao or '').strip().lower()
        if not permissao_limpa:
            return True
        return permissao_limpa in {item.strip().lower() for item in self.permissoes}

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'key': self.key,
            'permissoes': self.permissoes,
            'rate_limit': int(self.rate_limit or 0),
            'ativa': bool(self.ativa),
            'ultimo_uso': self.ultimo_uso.isoformat() if self.ultimo_uso else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expira_em': self.expira_em.isoformat() if self.expira_em else None,
        }
