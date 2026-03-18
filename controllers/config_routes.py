# ===========================================
# routes/config_routes.py - Rotas de Configuração
# ===========================================

from flask import Blueprint, request, jsonify
from extensions import db
import os
import logging
from infrastructure.backup_service import criar_backup_database, status_backups
from repositories import config_repository
from services.config_service import (
    enviar_relatorio_teste as enviar_relatorio_teste_service,
    obter_config_contador as obter_config_contador_service,
    salvar_config_contador,
)

config_bp = Blueprint('config', __name__, url_prefix='/api/config')
logger = logging.getLogger(__name__)

# ===========================================
# CONFIGURAÇÕES DO CONTADOR
# ===========================================

@config_bp.route('/contador', methods=['GET'])
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

# ===========================================
# HISTÓRICO DE ENVIOS
# ===========================================

@config_bp.route('/envios-relatorio', methods=['GET'])
def listar_envios():
    """Lista o histórico de envios de relatórios"""
    try:
        envios = config_repository.listar_envios(20)
        return jsonify([e.to_dict() for e in envios])
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@config_bp.route('/backup/status', methods=['GET'])
def backup_status():
    """Retorna status dos backups locais do banco."""
    try:
        dados = status_backups(prefixo='database_backup_', extensao='.db')
        dados['retencao_dias'] = int(os.environ.get('BACKUP_RETENTION_DAYS', '15'))
        return jsonify(dados)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@config_bp.route('/backup/executar', methods=['POST'])
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
