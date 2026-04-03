from datetime import datetime

from extensions import db


class Anexo(db.Model):
    __tablename__ = 'anexos'

    id = db.Column(db.Integer, primary_key=True)
    entidade_tipo = db.Column(db.String(50), nullable=False, index=True)
    entidade_id = db.Column(db.Integer, nullable=False, index=True)
    nome_arquivo = db.Column(db.String(200), nullable=False)
    caminho_arquivo = db.Column(db.String(500), nullable=False, unique=True)
    tamanho_bytes = db.Column(db.Integer, default=0)
    mime_type = db.Column(db.String(100))
    descricao = db.Column(db.String(200))
    categoria = db.Column(db.String(50), default='documento', index=True)
    usuario_id = db.Column(db.Integer, nullable=True)
    metadata_json = db.Column('metadata', db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'entidade_tipo': self.entidade_tipo,
            'entidade_id': self.entidade_id,
            'nome_arquivo': self.nome_arquivo,
            'nome_original': self.nome_arquivo,
            'caminho_arquivo': self.caminho_arquivo,
            'caminho_relativo': self.caminho_arquivo,
            'mime_type': self.mime_type,
            'tipo_mime': self.mime_type,
            'tamanho_bytes': self.tamanho_bytes,
            'descricao': self.descricao,
            'categoria': self.categoria,
            'usuario_id': self.usuario_id,
            'metadata': dict(self.metadata_json or {}),
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None,
        }
