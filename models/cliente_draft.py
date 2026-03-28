from datetime import datetime
from extensions import db


class ClienteDraft(db.Model):
    __tablename__ = 'clientes_draft'

    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(100))
    cpf = db.Column(db.String(14))

    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))

    endereco = db.Column(db.String(200))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(10))

    placa = db.Column(db.String(10))
    fabricante = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    ano = db.Column(db.String(4))
    motor = db.Column(db.String(50))
    combustivel = db.Column(db.String(30))
    cor = db.Column(db.String(30))
    tanque = db.Column(db.String(10))
    km = db.Column(db.Integer, default=0)
    direcao = db.Column(db.String(30))
    ar = db.Column(db.String(30))

    is_draft = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'nome_cliente': self.nome_cliente,
            'cpf': self.cpf,
            'telefone': self.telefone,
            'email': self.email,
            'endereco': self.endereco,
            'cidade': self.cidade,
            'estado': self.estado,
            'cep': self.cep,
            'placa': self.placa,
            'fabricante': self.fabricante,
            'modelo': self.modelo,
            'ano': self.ano,
            'motor': self.motor,
            'combustivel': self.combustivel,
            'cor': self.cor,
            'tanque': self.tanque,
            'km': self.km,
            'direcao': self.direcao,
            'ar': self.ar,
            'is_draft': self.is_draft,
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M') if self.updated_at else None,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }
