# ===========================================
# routes/config_routes.py - Rotas de Configuração
# ===========================================

from flask import Blueprint, request, jsonify
from extensions import db
from datetime import datetime, timedelta
import os
import logging
from services.backup_service import criar_backup_database, status_backups

config_bp = Blueprint('config', __name__, url_prefix='/api/config')
logger = logging.getLogger(__name__)

# ===========================================
# CONFIGURAÇÕES DO CONTADOR
# ===========================================

@config_bp.route('/contador', methods=['GET'])
def get_config_contador():
    """Retorna as configurações atuais do contador"""
    try:
        from models import ConfigContador
        config = ConfigContador.query.first()
        if not config:
            return jsonify({})
        return jsonify(config.to_dict())
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@config_bp.route('/contador', methods=['POST'])
def save_config_contador():
    """Salva as configurações do contador"""
    try:
        from models import ConfigContador
        dados = request.json
        config = ConfigContador.query.first()
        
        if not config:
            config = ConfigContador()
        
        config.email_cliente = dados.get('email_cliente', '')
        if dados.get('senha_app'):
            config.senha_app = dados.get('senha_app', '')
        config.email_contador = dados.get('email_contador', '')
        config.profissional_envio_auto = (dados.get('profissional_envio_auto') or '').strip() or None
        config.frequencia = dados.get('frequencia', 'diario')
        config.dia_envio = dados.get('dia_envio', 1)
        config.ativo = dados.get('ativo', True)
        
        if not config.id:
            db.session.add(config)
        
        db.session.commit()
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
        from models import Ordem, Cliente, Saida, EnvioRelatorio
        from services.relatorio_service import gerar_relatorio_html
        from services.email_service import enviar_relatorio_email
        
        dados = request.json
        periodo = dados.get('periodo', 'diario')
        formato = dados.get('formato', 'html')
        
        email_cliente = dados.get('email_cliente')
        senha_app = dados.get('senha_app')
        email_contador = dados.get('email_contador')
        
        if not email_cliente or not senha_app or not email_contador:
            return jsonify({'erro': 'E-mails e senha são obrigatórios'}), 400
        
        hoje = datetime.now()
        
        # Definir período
        if periodo == 'diario':
            data_inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
            nome_periodo = hoje.strftime('%d/%m/%Y')
        elif periodo == 'semanal':
            inicio_semana = hoje - timedelta(days=hoje.weekday())
            data_inicio = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
            nome_periodo = f"Semana de {inicio_semana.strftime('%d/%m')}"
        else:  # mensal
            data_inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            nome_periodo = hoje.strftime('%m/%Y')
        
        # Buscar entradas
        ordens_concluidas = Ordem.query.filter(
            Ordem.status == 'Concluído'
        ).all()
        
        entradas = []
        total_entradas = 0
        for o in ordens_concluidas:
            data_ordem = o.data_conclusao or o.data_retirada
            if data_ordem and data_ordem.date() >= data_inicio.date():
                cliente = Cliente.query.get(o.cliente_id)
                entradas.append({
                    'data': data_ordem.strftime('%d/%m/%Y'),
                    'cliente': cliente.nome_cliente if cliente else '---',
                    'servico': o.diagnostico[:50] + '...' if o.diagnostico and len(o.diagnostico) > 50 else o.diagnostico or '---',
                    'valor': o.total_geral,
                    'pagamento': o.forma_pagamento or '---'
                })
                total_entradas += o.total_geral
        
        # Buscar saídas
        saidas_db = Saida.query.filter(Saida.data >= data_inicio.date()).all()
        saidas = []
        total_saidas = 0
        for s in saidas_db:
            saidas.append({
                'data': s.data.strftime('%d/%m/%Y') if s.data else None,
                'categoria': s.categoria or 'Outros',
                'descricao': s.descricao,
                'valor': s.valor
            })
            total_saidas += s.valor
        
        saldo = total_entradas - total_saidas
        
        # Gerar HTML do relatório
        html = gerar_relatorio_html(
            periodo=nome_periodo,
            entradas=entradas,
            saidas=saidas,
            total_entradas=total_entradas,
            total_saidas=total_saidas,
            saldo=saldo
        )
        
        # Enviar e-mail
        sucesso, msg = enviar_relatorio_email(
            email_cliente, 
            senha_app, 
            email_contador, 
            nome_periodo, 
            html, 
            formato
        )
        
        if sucesso:
            return jsonify({'mensagem': f'Relatório {formato} enviado com sucesso'})
        else:
            return jsonify({'erro': msg}), 500
            
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
        from models import EnvioRelatorio
        envios = EnvioRelatorio.query.order_by(
            EnvioRelatorio.data_envio.desc()
        ).limit(20).all()
        
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
        from models import AuditoriaEvento
        limite = request.args.get('limite', '50')
        try:
            limite_int = max(1, min(200, int(limite)))
        except ValueError:
            limite_int = 50

        eventos = (
            AuditoriaEvento.query
            .order_by(AuditoriaEvento.data_evento.desc())
            .limit(limite_int)
            .all()
        )
        return jsonify([e.to_dict() for e in eventos])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
