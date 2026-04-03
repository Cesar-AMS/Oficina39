# ===========================================
# routes/config_routes.py - Rotas de Configuração
# ===========================================

from flask import Blueprint, request, jsonify, current_app
from extensions import db
import os
import logging
import uuid
from werkzeug.utils import secure_filename
from .auth_utils import require_profiles
from infrastructure.backup_service import criar_backup_database, status_backups
from repositories import config_repository
from services.config_service import (
    enviar_relatorio_teste as enviar_relatorio_teste_service,
    obter_config_contador as obter_config_contador_service,
    salvar_config_contador,
)

config_bp = Blueprint('config', __name__, url_prefix='/api/config')
logger = logging.getLogger(__name__)
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}


def _arquivo_permitido(nome_arquivo):
    return '.' in nome_arquivo and nome_arquivo.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

# ===========================================
# CONFIGURAÇÕES DO CONTADOR
# ===========================================

@config_bp.route('/contador', methods=['GET'])
@require_profiles('admin', 'gerente')
def get_config_contador():
    """Retorna as configurações atuais do contador"""
    try:
        config = obter_config_contador_service()
        if not config:
            return jsonify({})
        return jsonify(config.to_dict_completo())
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@config_bp.route('/contador', methods=['POST'])
@require_profiles('admin', 'gerente')
def save_config_contador():
    """Salva as configurações do contador"""
    try:
        config = salvar_config_contador(request.json or {})
        logger.info(
            "Config contador atualizada (email_cliente=%s, email_contador=%s, profissional_envio_auto=%s, frequencia=%s, ativo=%s)",
            config.email_cliente or '---',
            config.email_contador or '---',
            config.profissional_envio_auto or '---',
            config.frequencia or '---',
            bool(config.ativo)
        )
        return jsonify(config.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# ENVIO DE RELATÓRIOS
# ===========================================

@config_bp.route('/enviar-relatorio-teste', methods=['POST'])
@require_profiles('admin', 'gerente')
def enviar_relatorio_teste():
    """Envia um relatório de teste por e-mail"""
    try:
        sucesso, msg = enviar_relatorio_teste_service(request.json or {})
        
        if sucesso:
            return jsonify({'mensagem': 'Relatório enviado com sucesso'})
        else:
            return jsonify({'erro': msg}), 500
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@config_bp.route('/branding/logo-upload', methods=['POST'])
@require_profiles('admin', 'gerente')
def upload_logo_branding():
    """Recebe a logo ou QR code de personalização."""
    try:
        arquivo = request.files.get('arquivo')
        destino = (request.form.get('destino') or 'logo').strip().lower()
        if not arquivo or not arquivo.filename:
            return jsonify({'erro': 'Selecione uma imagem para enviar.'}), 400

        if not _arquivo_permitido(arquivo.filename):
            return jsonify({'erro': 'Formato inválido. Use PNG, JPG, JPEG, WEBP ou GIF.'}), 400

        if destino not in {'logo', 'qrcode1', 'qrcode2'}:
            return jsonify({'erro': 'Destino de upload inválido.'}), 400

        nome_original = secure_filename(arquivo.filename)
        extensao = os.path.splitext(nome_original)[1].lower()
        prefixo = {
            'logo': 'cliente_logo',
            'qrcode1': 'cliente_qrcode_1',
            'qrcode2': 'cliente_qrcode_2'
        }[destino]
        nome_final = f"{prefixo}_{uuid.uuid4().hex[:12]}{extensao}"
        pasta_destino = current_app.config['BRANDING_UPLOAD_FOLDER']
        os.makedirs(pasta_destino, exist_ok=True)
        caminho_destino = os.path.join(pasta_destino, nome_final)
        arquivo.save(caminho_destino)

        caminho_publico = f"/static/uploads/branding/{nome_final}"
        resposta = {
            'mensagem': 'Imagem enviada com sucesso.',
            'destino': destino,
            'arquivo_path': caminho_publico
        }
        if destino == 'logo':
            resposta['logo_index_path'] = caminho_publico
        elif destino == 'qrcode1':
            resposta['qrcode_1_path'] = caminho_publico
        else:
            resposta['qrcode_2_path'] = caminho_publico
        return jsonify(resposta)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===========================================
# HISTÓRICO DE ENVIOS
# ===========================================

@config_bp.route('/envios-relatorio', methods=['GET'])
@require_profiles('admin', 'gerente')
def listar_envios():
    """Lista o histórico de envios de relatórios"""
    try:
        envios = config_repository.listar_envios(20)
        return jsonify([e.to_dict() for e in envios])
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@config_bp.route('/backup/status', methods=['GET'])
@require_profiles('admin', 'gerente')
def backup_status():
    """Retorna status dos backups locais do banco."""
    try:
        dados = status_backups(prefixo='database_backup_', extensao='.db')
        dados['retencao_dias'] = int(os.environ.get('BACKUP_RETENTION_DAYS', '15'))
        return jsonify(dados)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@config_bp.route('/backup/executar', methods=['POST'])
@require_profiles('admin', 'gerente')
def backup_executar():
    """Executa backup manual imediato com mesma política de retenção."""
    try:
        retencao_dias = int(os.environ.get('BACKUP_RETENTION_DAYS', '15'))
        info = criar_backup_database(prefixo='database_backup_', dias_retencao=retencao_dias)
        return jsonify({
            'mensagem': 'Backup executado com sucesso.',
            'arquivo': info['arquivo'],
            'tamanho_bytes': info['tamanho_bytes'],
            'removidos_por_retencao': info['removidos_por_retencao']
        })
    except FileNotFoundError as e:
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@config_bp.route('/auditoria-eventos', methods=['GET'])
@require_profiles('admin', 'gerente')
def listar_auditoria_eventos():
    """Lista eventos de auditoria operacional recentes."""
    try:
        limite = request.args.get('limite', '50')
        try:
            limite_int = max(1, min(200, int(limite)))
        except ValueError:
            limite_int = 50

        eventos = config_repository.listar_auditoria_eventos(limite_int)
        return jsonify([e.to_dict() for e in eventos])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
