# ===========================================
# controllers/clientes_routes.py - Controller de Clientes
# ===========================================

from flask import Blueprint, request, jsonify, send_file
from extensions import db
from .auth_utils import require_auth
from repositories import cliente_repository
from services.anexo_service import excluir_anexo, listar_anexos, obter_anexo, resolver_caminho_absoluto, salvar_anexo
from services.cliente_service import create_client
from utils.formatters import texto_limpo

clientes_bp = Blueprint('clientes', __name__, url_prefix='/api/clientes')

# ===========================================
# LISTAR TODOS OS CLIENTES
# ===========================================
@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    try:
        clientes = cliente_repository.listar_todos()
        return jsonify([c.to_dict() for c in clientes])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@clientes_bp.route('/<int:id>/anexos', methods=['GET'])
def listar_anexos_cliente(id):
    try:
        cliente = cliente_repository.buscar_por_id(id)
        if not cliente:
            return jsonify({'erro': 'Cliente nao encontrado'}), 404
        anexos = listar_anexos('cliente', id)
        return jsonify([a.to_dict() for a in anexos])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@clientes_bp.route('/<int:id>/anexos', methods=['POST'])
@require_auth
def upload_anexo_cliente(id):
    try:
        cliente = cliente_repository.buscar_por_id(id)
        if not cliente:
            return jsonify({'erro': 'Cliente nao encontrado'}), 404
        anexo = salvar_anexo(
            entidade_tipo='cliente',
            entidade_id=id,
            arquivo=request.files.get('arquivo'),
            descricao=request.form.get('descricao'),
            categoria=request.form.get('categoria', 'documento'),
        )
        return jsonify(anexo.to_dict()), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@clientes_bp.route('/<int:id>/anexos/<int:anexo_id>/download', methods=['GET'])
def download_anexo_cliente(id, anexo_id):
    try:
        cliente = cliente_repository.buscar_por_id(id)
        if not cliente:
            return jsonify({'erro': 'Cliente nao encontrado'}), 404
        anexo = obter_anexo('cliente', id, anexo_id)
        if not anexo:
            return jsonify({'erro': 'Anexo nao encontrado.'}), 404
        caminho_abs = resolver_caminho_absoluto(anexo)
        return send_file(caminho_abs, as_attachment=True, download_name=getattr(anexo, 'nome_arquivo', None) or getattr(anexo, 'nome_original', 'anexo'))
    except FileNotFoundError as e:
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@clientes_bp.route('/<int:id>/anexos/<int:anexo_id>', methods=['DELETE'])
@require_auth
def excluir_anexo_cliente(id, anexo_id):
    try:
        cliente = cliente_repository.buscar_por_id(id)
        if not cliente:
            return jsonify({'erro': 'Cliente nao encontrado'}), 404
        excluir_anexo('cliente', id, anexo_id)
        return jsonify({'mensagem': 'Anexo removido com sucesso.'})
    except LookupError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# BUSCAR CLIENTE POR ID
# ===========================================
@clientes_bp.route('/<int:id>', methods=['GET'])
def buscar_cliente(id):
    try:
        cliente = cliente_repository.buscar_por_id(id)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        return jsonify(cliente.to_dict())
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===========================================
# CRIAR NOVO CLIENTE
# ===========================================
@clientes_bp.route('/', methods=['POST'])
@require_auth
def criar_cliente():
    try:
        from models import Cliente
        dados = request.json or {}
        
        # If a draft_id is provided, promote the draft to a final Cliente
        draft_id = dados.get('draft_id')
        if draft_id:
            from models import ClienteDraft
            draft = db.session.get(ClienteDraft, draft_id)
            if not draft:
                return jsonify({'erro': 'Rascunho não encontrado'}), 404
            # merge draft fields into dados so validations below apply
            for f in ['nome_cliente','cpf','telefone','email','endereco','cidade','estado','cep',
                      'placa','fabricante','modelo','ano','motor','combustivel','cor','tanque','km','direcao','ar']:
                if getattr(draft, f, None) is not None and f not in dados:
                    dados[f] = getattr(draft, f)

        if not texto_limpo(dados.get('nome_cliente')):
            return jsonify({'erro': 'Nome é obrigatório'}), 400
        if not texto_limpo(dados.get('cpf')):
            return jsonify({'erro': 'CPF é obrigatório'}), 400
        
        if cliente_repository.buscar_por_cpf(dados['cpf']):
            return jsonify({'erro': 'CPF já cadastrado'}), 400
        
        cliente = create_client(dados)

        # If we promoted from a draft, remove the draft to keep DB tidy
        if draft_id:
            try:
                draft = db.session.get(ClienteDraft, draft_id)
                if draft:
                    db.session.delete(draft)
                    db.session.commit()
            except Exception:
                # non-fatal: ignore deletion errors but don't fail creation
                db.session.rollback()

        return jsonify(cliente.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# ATUALIZAR CLIENTE
# ===========================================
@clientes_bp.route('/<int:id>', methods=['PUT'])
@require_auth
def atualizar_cliente(id):
    try:
        from models import Cliente
        cliente = cliente_repository.buscar_por_id(id)
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        dados = request.json
        
        # ===== NOVOS CAMPOS ADICIONADOS =====
        if 'nome_cliente' in dados:
            cliente.nome_cliente = dados['nome_cliente']
        if 'cpf' in dados:
            cpf_novo = (dados.get('cpf') or '').strip()
            if not cpf_novo:
                return jsonify({'erro': 'CPF é obrigatório'}), 400
            outro_cliente = Cliente.query.filter(Cliente.cpf == cpf_novo, Cliente.id != id).first()
            if outro_cliente:
                return jsonify({'erro': 'CPF já cadastrado'}), 400
            cliente.cpf = cpf_novo
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
@require_auth
def deletar_cliente(id):
    try:
        cliente = cliente_repository.buscar_por_id(id)
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
        termo = (request.args.get('termo', '') or '').strip()
        
        if not termo:
            return jsonify([])

        clientes = cliente_repository.buscar_por_termo(termo)
        
        return jsonify([c.to_dict() for c in clientes])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ===========================================
# SALVAR RASCUNHO / DADOS PARCIAIS (sem validações obrigatórias)
# ===========================================
@clientes_bp.route('/draft', methods=['POST'])
@require_auth
def salvar_rascunho():
    try:
        # Persistir rascunhos em tabela separada ClienteDraft
        from models import ClienteDraft
        dados = request.json or {}

        draft_id = dados.get('id')
        if draft_id:
            draft = db.session.get(ClienteDraft, draft_id)
            # se não existir, criamos um novo rascunho
            if not draft:
                draft = ClienteDraft()
        else:
            draft = ClienteDraft()

        # Atribui apenas os campos recebidos (sem validação estrita)
        campos = ['nome_cliente', 'cpf', 'telefone', 'email', 'endereco', 'cidade', 'estado', 'cep',
                  'placa', 'fabricante', 'modelo', 'ano', 'motor', 'combustivel', 'cor', 'tanque', 'km', 'direcao', 'ar']
        for campo in campos:
            if campo in dados:
                setattr(draft, campo, dados.get(campo))

        # Garantir flag de rascunho
        draft.is_draft = True

        if not draft.id:
            db.session.add(draft)

        db.session.commit()
        return jsonify(draft.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


# ===========================================
# ROTAS PARA RASCUNHOS
# ===========================================
@clientes_bp.route('/drafts', methods=['GET'])
def listar_rascunhos():
    try:
        from models import ClienteDraft
        drafts = ClienteDraft.query.order_by(ClienteDraft.updated_at.desc()).all()
        return jsonify([d.to_dict() for d in drafts])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@clientes_bp.route('/draft/<int:id>', methods=['GET'])
def obter_rascunho(id):
    try:
        from models import ClienteDraft
        draft = db.session.get(ClienteDraft, id)
        if not draft:
            return jsonify({'erro': 'Rascunho não encontrado'}), 404
        return jsonify(draft.to_dict())
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
