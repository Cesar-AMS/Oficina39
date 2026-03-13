# ===========================================
# routes/clientes_routes.py - Rotas de Clientes
# ===========================================

from flask import Blueprint, request, jsonify
from extensions import db
from sqlalchemy import or_, func

clientes_bp = Blueprint('clientes', __name__, url_prefix='/api/clientes')

# ===========================================
# LISTAR TODOS OS CLIENTES
# ===========================================
@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    try:
        from models import Cliente
        clientes = Cliente.query.all()
        return jsonify([c.to_dict() for c in clientes])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===========================================
# BUSCAR CLIENTE POR ID
# ===========================================
@clientes_bp.route('/<int:id>', methods=['GET'])
def buscar_cliente(id):
    try:
        from models import Cliente
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        return jsonify(cliente.to_dict())
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===========================================
# CRIAR NOVO CLIENTE
# ===========================================
@clientes_bp.route('/', methods=['POST'])
def criar_cliente():
    try:
        from models import Cliente
        dados = request.json
        
        if not dados.get('nome_cliente'):
            return jsonify({'erro': 'Nome é obrigatório'}), 400
        if not dados.get('cpf'):
            return jsonify({'erro': 'CPF é obrigatório'}), 400
        
        if Cliente.query.filter_by(cpf=dados['cpf']).first():
            return jsonify({'erro': 'CPF já cadastrado'}), 400
        
        cliente = Cliente(
            nome_cliente=dados['nome_cliente'],
            cpf=dados['cpf'],
            
            # ===== NOVOS CAMPOS =====
            telefone=dados.get('telefone', ''),
            email=dados.get('email', ''),
            
            endereco=dados.get('endereco', ''),
            cidade=dados.get('cidade', ''),
            estado=dados.get('estado', ''),
            cep=dados.get('cep', ''),
            
            placa=dados.get('placa', ''),
            fabricante=dados.get('fabricante', ''),
            modelo=dados.get('modelo', ''),
            ano=dados.get('ano', ''),
            motor=dados.get('motor', ''),
            combustivel=dados.get('combustivel', ''),
            cor=dados.get('cor', ''),
            tanque=dados.get('tanque', ''),
            km=dados.get('km', 0),
            direcao=dados.get('direcao', ''),
            ar=dados.get('ar', '')
        )
        
        db.session.add(cliente)
        db.session.commit()
        
        return jsonify(cliente.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# ATUALIZAR CLIENTE
# ===========================================
@clientes_bp.route('/<int:id>', methods=['PUT'])
def atualizar_cliente(id):
    try:
        from models import Cliente
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        dados = request.json
        
        # ===== NOVOS CAMPOS ADICIONADOS =====
        if 'nome_cliente' in dados:
            cliente.nome_cliente = dados['nome_cliente']
        if 'telefone' in dados:
            cliente.telefone = dados['telefone']
        if 'email' in dados:
            cliente.email = dados['email']
        if 'endereco' in dados:
            cliente.endereco = dados['endereco']
        if 'cidade' in dados:
            cliente.cidade = dados['cidade']
        if 'estado' in dados:
            cliente.estado = dados['estado']
        if 'cep' in dados:
            cliente.cep = dados['cep']
        if 'placa' in dados:
            cliente.placa = dados['placa']
        if 'fabricante' in dados:
            cliente.fabricante = dados['fabricante']
        if 'modelo' in dados:
            cliente.modelo = dados['modelo']
        if 'ano' in dados:
            cliente.ano = dados['ano']
        if 'motor' in dados:
            cliente.motor = dados['motor']
        if 'combustivel' in dados:
            cliente.combustivel = dados['combustivel']
        if 'cor' in dados:
            cliente.cor = dados['cor']
        if 'tanque' in dados:
            cliente.tanque = dados['tanque']
        if 'km' in dados:
            cliente.km = dados['km']
        if 'direcao' in dados:
            cliente.direcao = dados['direcao']
        if 'ar' in dados:
            cliente.ar = dados['ar']
        
        db.session.commit()
        return jsonify(cliente.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# DELETAR CLIENTE
# ===========================================
@clientes_bp.route('/<int:id>', methods=['DELETE'])
def deletar_cliente(id):
    try:
        from models import Cliente
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        db.session.delete(cliente)
        db.session.commit()
        return jsonify({'mensagem': 'Cliente removido com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# BUSCAR CLIENTES POR TERMO
# ===========================================
@clientes_bp.route('/busca', methods=['GET'])
def buscar_clientes():
    try:
        from models import Cliente
        termo = (request.args.get('termo', '') or '').strip()
        
        if not termo:
            return jsonify([])

        termo_numerico = ''.join(ch for ch in termo if ch.isdigit())
        cpf_sem_mascara = func.replace(func.replace(func.replace(Cliente.cpf, '.', ''), '-', ''), '/', '')
        condicoes = [
            Cliente.nome_cliente.ilike(f'%{termo}%'),
            Cliente.cpf.ilike(f'%{termo}%')
        ]
        if termo_numerico:
            condicoes.append(cpf_sem_mascara.ilike(f'%{termo_numerico}%'))

        clientes = Cliente.query.filter(or_(*condicoes)).limit(10).all()
        
        return jsonify([c.to_dict() for c in clientes])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
