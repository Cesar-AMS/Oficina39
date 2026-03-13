# ===========================================
# models/ordem_anexo.py - Anexos da Ordem de Serviço
# ===========================================

from datetime import datetime
from extensions import db


class OrdemAnexo(db.Model):
    __tablename__ = 'ordem_anexos'

    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey('ordens.id'), nullable=False, index=True)
    nome_original = db.Column(db.String(255), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False, unique=True)
    caminho_relativo = db.Column(db.String(255), nullable=False)
    tipo_mime = db.Column(db.String(120))
    tamanho_bytes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    ordem = db.relationship('Ordem', back_populates='anexos')

    def to_dict(self):
        return {
            'id': self.id,
            'ordem_id': self.ordem_id,
            'nome_original': self.nome_original,
            'nome_arquivo': self.nome_arquivo,
            'caminho_relativo': self.caminho_relativo,
            'tipo_mime': self.tipo_mime,
            'tamanho_bytes': self.tamanho_bytes,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }
