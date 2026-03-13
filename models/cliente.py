# ===========================================
# models/cliente.py - Modelo de Cliente
# ===========================================

from datetime import datetime
from extensions import db

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    
    # ===== NOVOS CAMPOS =====
    telefone = db.Column(db.String(20))        # ← ADICIONADO
    email = db.Column(db.String(100))          # ← ADICIONADO
    
    endereco = db.Column(db.String(200))
    cidade = db.Column(db.String(100))         # ← ADICIONADO
    estado = db.Column(db.String(2))           # ← ADICIONADO
    cep = db.Column(db.String(10))             # ← ADICIONADO
    
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
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relacionamento com ordens
    ordens = db.relationship('Ordem', back_populates='cliente', lazy='dynamic')
    
    def to_dict(self):
        """Converte o objeto para dicionário (para JSON)"""
        return {
            'id': self.id,
            'nome_cliente': self.nome_cliente,
            'cpf': self.cpf,
            # ===== NOVOS CAMPOS NO to_dict =====
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
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Cliente {self.nome_cliente}>'