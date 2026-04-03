# ===========================================
# controllers/ordens_routes.py - Controller de Ordens de Servico
# ===========================================

import io
import logging
import os

from flask import Blueprint, jsonify, request, send_file

from extensions import db
from .auth_utils import require_auth
from repositories import cliente_repository, ordem_repository
from services.anexo_service import (
    excluir_anexo as excluir_anexo_generico,
    resolver_caminho_absoluto,
    salvar_anexo,
)
from services.debito_service import faturar_ordem_no_caixa
from services.ordem_service import (
    atualizar_ordem as atualizar_ordem_service,
    atualizar_status as atualizar_status_service,
    criar_ordem as criar_ordem_service,
    deletar_ordem as deletar_ordem_service,
    duplicar_ordem as duplicar_ordem_service,
    parse_data_iso,
    reabrir_ordem as reabrir_ordem_service,
)
from services.order_pdf_service import (
    build_order_whatsapp_web_url,
    generate_order_preview_pdf_bytes,
    suggested_preview_pdf_name,
)

ordens_bp = Blueprint('ordens', __name__, url_prefix='/api/ordens')
logger = logging.getLogger(__name__)


@ordens_bp.route('/', methods=['GET'])
def listar_ordens():
    try:
        ordens = ordem_repository.listar_todas()
        return jsonify([o.to_dict() for o in ordens])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>', methods=['GET'])
def buscar_ordem(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem nao encontrada'}), 404

        dados = ordem.to_dict()
        cliente = cliente_repository.buscar_por_id(ordem.cliente_id)
        dados['cliente'] = cliente.to_dict() if cliente else {}
        return jsonify(dados)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/', methods=['POST'])
@require_auth
def criar_ordem():
    try:
        ordem = criar_ordem_service(request.json or {}, request)
        dados = ordem.to_dict()
        dados['preview_pdf_url'] = f"/api/export/gerar-pdf/{ordem.id}?inline=1"
        dados['download_pdf_url'] = f"/api/export/gerar-pdf/{ordem.id}"
        try:
            dados['whatsapp_web_url'] = build_order_whatsapp_web_url(ordem.id)
        except Exception:
            dados['whatsapp_web_url'] = None
        return jsonify(dados), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except LookupError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/preview', methods=['POST'])
@require_auth
def preview_ordem():
    try:
        pdf_bytes = generate_order_preview_pdf_bytes(request.get_json() or {})
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=False,
            download_name=suggested_preview_pdf_name(),
        )
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except LookupError as e:
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/whatsapp-link', methods=['GET'])
@require_auth
def obter_link_whatsapp(id):
    try:
        return jsonify({'url': build_order_whatsapp_web_url(id)})
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except LookupError as e:
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>', methods=['PUT'])
@require_auth
def atualizar_ordem(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem nao encontrada'}), 404

        dados = request.json or {}
        profissional_anterior = atualizar_ordem_service(ordem, dados, request)
        if 'profissional_responsavel' in dados and (ordem.profissional_responsavel or '').strip() != profissional_anterior:
            logger.info(
                "OS %s: profissional alterado de '%s' para '%s'",
                ordem.id,
                profissional_anterior or '---',
                (ordem.profissional_responsavel or '').strip() or '---',
            )

        return jsonify(ordem.to_dict())
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/status', methods=['PATCH'])
@require_auth
def atualizar_status(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem nao encontrada'}), 404

        dados = request.json or {}
        status_anterior = atualizar_status_service(ordem, dados, request)
        logger.info(
            "OS %s: status alterado de '%s' para '%s' (forma_pagamento=%s)",
            ordem.id,
            status_anterior or '---',
            ordem.status,
            ordem.forma_pagamento or '---',
        )
        return jsonify({'mensagem': 'Status atualizado', 'status': ordem.status, 'forma_pagamento': ordem.forma_pagamento})
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/faturamento', methods=['POST'])
@require_auth
def faturar_ordem(id):
    try:
        ordem = faturar_ordem_no_caixa(id, request.json or {}, request)
        return jsonify(ordem.to_dict())
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except LookupError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>', methods=['DELETE'])
@require_auth
def deletar_ordem(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem nao encontrada'}), 404
        deletar_ordem_service(ordem, request)
        return jsonify({'mensagem': 'Ordem removida com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/reabrir', methods=['POST'])
@require_auth
def reabrir_ordem(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem nao encontrada'}), 404

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
            return jsonify({'erro': 'Ordem nao encontrada'}), 404

        logs = ordem_repository.listar_logs_status(id)
        return jsonify([log.to_dict() for log in logs])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/duplicar', methods=['POST'])
@require_auth
def duplicar_ordem(id):
    try:
        origem = ordem_repository.buscar_por_id(id)
        if not origem:
            return jsonify({'erro': 'Ordem nao encontrada'}), 404
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
            return jsonify({'erro': 'Ordem nao encontrada'}), 404
        anexos = ordem_repository.listar_anexos(id)
        return jsonify([a.to_dict() for a in anexos])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/anexos', methods=['POST'])
@require_auth
def upload_anexo(id):
    try:
        ordem = ordem_repository.buscar_por_id(id)
        if not ordem:
            return jsonify({'erro': 'Ordem nao encontrada'}), 404

        anexo = salvar_anexo(
            entidade_tipo='ordem',
            entidade_id=id,
            arquivo=request.files.get('arquivo'),
            descricao=request.form.get('descricao'),
            categoria=request.form.get('categoria', 'documento'),
        )
        return jsonify(anexo.to_dict()), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/anexos/<int:anexo_id>/download', methods=['GET'])
def download_anexo(id, anexo_id):
    try:
        anexo = ordem_repository.buscar_anexo(id, anexo_id)
        if not anexo:
            return jsonify({'erro': 'Anexo nao encontrado.'}), 404

        caminho_abs = resolver_caminho_absoluto(anexo)
        if not os.path.exists(caminho_abs):
            return jsonify({'erro': 'Arquivo fisico nao encontrado.'}), 404

        nome_download = getattr(anexo, 'nome_arquivo', None) or getattr(anexo, 'nome_original', 'anexo')
        return send_file(caminho_abs, as_attachment=True, download_name=nome_download)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/anexos/<int:anexo_id>', methods=['DELETE'])
@require_auth
def excluir_anexo(id, anexo_id):
    try:
        excluir_anexo_generico('ordem', id, anexo_id)
        return jsonify({'mensagem': 'Anexo removido com sucesso.'})
    except LookupError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


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
            data_fim=dt_fim,
        )
        return jsonify([o.to_dict() for o in ordens])
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
