# ===========================================
# controllers/ordens_routes.py - Controller de Ordens de Serviço
# ===========================================

from flask import Blueprint, request, jsonify, send_file
from extensions import db
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from repositories import cliente_repository, ordem_repository
from services.ordem_service import (
    atualizar_ordem as atualizar_ordem_service,
    atualizar_status as atualizar_status_service,
    criar_ordem as criar_ordem_service,
    deletar_ordem as deletar_ordem_service,
    duplicar_ordem as duplicar_ordem_service,
    parse_data_iso,
    reabrir_ordem as reabrir_ordem_service,
)

ordens_bp = Blueprint('ordens', __name__, url_prefix='/api/ordens')
logger = logging.getLogger(__name__)

EXTENSOES_ANEXO = {'.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.xlsx', '.xls', '.txt'}

# ===========================================
# LISTAR TODAS AS ORDENS
# ===========================================
@ordens_bp.route('/', methods=['GET'])
def listar_ordens():
    try:
        ordens = ordem_repository.listar_todas()
        return jsonify([o.to_dict() for o in ordens])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===========================================
# BUSCAR ORDEM POR ID
# ===========================================
@ordens_bp.route('/<int:id>', methods=['GET'])
def buscar_ordem(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404
        
        dados = ordem.to_dict()
        cliente = cliente_repository.buscar_por_id(ordem.cliente_id)
        if cliente:
            dados['cliente'] = cliente.to_dict()
        else:
            dados['cliente'] = {}
        
        return jsonify(dados)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===========================================
# CRIAR NOVA ORDEM
# ===========================================
@ordens_bp.route('/', methods=['POST'])
def criar_ordem():
    try:
        ordem = criar_ordem_service(request.json or {}, request)
        return jsonify(ordem.to_dict()), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except LookupError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# ATUALIZAR ORDEM (PUT)
# ===========================================
@ordens_bp.route('/<int:id>', methods=['PUT'])
def atualizar_ordem(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404
        dados = request.json or {}
        profissional_anterior = atualizar_ordem_service(ordem, dados, request)
        if 'profissional_responsavel' in dados and (ordem.profissional_responsavel or '').strip() != profissional_anterior:
            logger.info(
                "OS %s: profissional alterado de '%s' para '%s'",
                ordem.id,
                profissional_anterior or '---',
                (ordem.profissional_responsavel or '').strip() or '---'
            )
        
        return jsonify(ordem.to_dict())
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# ATUALIZAR STATUS DA ORDEM (PATCH)
# ===========================================
@ordens_bp.route('/<int:id>/status', methods=['PATCH'])
def atualizar_status(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404
        dados = request.json or {}
        status_anterior = atualizar_status_service(ordem, dados, request)
        logger.info(
            "OS %s: status alterado de '%s' para '%s' (forma_pagamento=%s)",
            ordem.id,
            status_anterior or '---',
            ordem.status,
            ordem.forma_pagamento or '---'
        )
        
        return jsonify({'mensagem': 'Status atualizado', 'status': ordem.status, 'forma_pagamento': ordem.forma_pagamento})
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# DELETAR ORDEM
# ===========================================
@ordens_bp.route('/<int:id>', methods=['DELETE'])
def deletar_ordem(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404
        deletar_ordem_service(ordem, request)
        return jsonify({'mensagem': 'Ordem removida com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/reabrir', methods=['POST'])
def reabrir_ordem(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404

        reabrir_ordem_service(ordem, request)
        return jsonify({'mensagem': 'Ordem reaberta com sucesso.', 'status': ordem.status})
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/status-log', methods=['GET'])
def listar_log_status(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404

        logs = ordem_repository.listar_logs_status(id)
        return jsonify([log.to_dict() for log in logs])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/duplicar', methods=['POST'])
def duplicar_ordem(id):
    try:
        origem = ordem_repository.buscar_por_id(id)
        if not origem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404
        nova = duplicar_ordem_service(origem, request)
        return jsonify({'mensagem': 'Ordem duplicada com sucesso.', 'nova_ordem_id': nova.id, 'ordem': nova.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/anexos', methods=['GET'])
def listar_anexos(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404
        anexos = ordem_repository.listar_anexos(id)
        return jsonify([a.to_dict() for a in anexos])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/anexos', methods=['POST'])
def upload_anexo(id):
    try:
        from models import OrdemAnexo
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404

        arquivo = request.files.get('arquivo')
        if not arquivo or not arquivo.filename:
            return jsonify({'erro': 'Arquivo não enviado.'}), 400

        nome_original = arquivo.filename
        nome_seguro = secure_filename(nome_original)
        ext = os.path.splitext(nome_seguro)[1].lower()
        if ext not in EXTENSOES_ANEXO:
            return jsonify({'erro': 'Tipo de arquivo não permitido.'}), 400

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        pasta_rel = os.path.join('uploads', 'ordens', str(id))
        pasta_abs = os.path.join(base_dir, pasta_rel)
        os.makedirs(pasta_abs, exist_ok=True)

        nome_final = f'{uuid.uuid4().hex}{ext}'
        caminho_abs = os.path.join(pasta_abs, nome_final)
        arquivo.save(caminho_abs)

        anexo = OrdemAnexo(
            ordem_id=id,
            nome_original=nome_original,
            nome_arquivo=nome_final,
            caminho_relativo=os.path.join(pasta_rel, nome_final).replace('\\', '/'),
            tipo_mime=arquivo.mimetype or '',
            tamanho_bytes=os.path.getsize(caminho_abs)
        )
        db.session.add(anexo)
        db.session.commit()
        return jsonify(anexo.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/anexos/<int:anexo_id>/download', methods=['GET'])
def download_anexo(id, anexo_id):
    try:
        anexo = ordem_repository.buscar_anexo(id, anexo_id)
        if not anexo:
            return jsonify({'erro': 'Anexo não encontrado.'}), 404

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        caminho_abs = os.path.join(base_dir, anexo.caminho_relativo.replace('/', os.sep))
        if not os.path.exists(caminho_abs):
            return jsonify({'erro': 'Arquivo físico não encontrado.'}), 404

        return send_file(caminho_abs, as_attachment=True, download_name=anexo.nome_original)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/anexos/<int:anexo_id>', methods=['DELETE'])
def excluir_anexo(id, anexo_id):
    try:
        anexo = ordem_repository.buscar_anexo(id, anexo_id)
        if not anexo:
            return jsonify({'erro': 'Anexo não encontrado.'}), 404

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        caminho_abs = os.path.join(base_dir, anexo.caminho_relativo.replace('/', os.sep))
        if os.path.exists(caminho_abs):
            try:
                os.remove(caminho_abs)
            except Exception:
                pass

        db.session.delete(anexo)
        db.session.commit()
        return jsonify({'mensagem': 'Anexo removido com sucesso.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


# ===========================================
# BUSCAR ORDENS POR CLIENTE OU STATUS
# ===========================================
@ordens_bp.route('/busca', methods=['GET'])
def buscar_ordens():
    try:
        cliente = request.args.get('cliente', '')
        status = request.args.get('status', '')
        profissional = request.args.get('profissional', '')
        forma_pagamento = request.args.get('forma_pagamento', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')

        dt_inicio = parse_data_iso(data_inicio) if data_inicio else None
        dt_fim = parse_data_iso(data_fim).replace(hour=23, minute=59, second=59, microsecond=999999) if data_fim else None
        ordens = ordem_repository.buscar_por_filtros(
            cliente=cliente,
            status=status,
            profissional=profissional,
            forma_pagamento=forma_pagamento,
            data_inicio=dt_inicio,
            data_fim=dt_fim
        )
        return jsonify([o.to_dict() for o in ordens])
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
