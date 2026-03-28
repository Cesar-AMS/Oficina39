# ===========================================
# app.py - Arquivo Principal do Sistema
# ===========================================

from flask import Flask
from extensions import db, mail, scheduler
from controllers import blueprints
import os
import atexit
from sqlalchemy import inspect, text
from infrastructure.backup_service import criar_backup_database

# ===========================================
# CRIAR A APLICAÇÃO
# ===========================================
def create_app(testing: bool = False, start_scheduler: bool = True):
    # Caminho absoluto para a pasta static
    basedir = os.path.abspath(os.path.dirname(__file__))
    static_dir = os.path.join(basedir, 'static')
    
    views_dir = os.path.join(basedir, 'views')

    # Criar app com pasta estática configurada
    app = Flask(__name__, 
                template_folder=views_dir,
                static_folder=static_dir,
                static_url_path='/static')
    
    # Carregar variáveis de ambiente (opcional .env)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        # python-dotenv é opcional; se não disponível, seguimos com env vars do sistema
        pass

    # Configurações
    # Permitir modo de teste com banco em memória para os testes automatizados
    if testing or os.environ.get('TESTING') == '1':
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if os.environ.get('OFICINA39_USE_WEBVIEW') == '1':
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Configurações de e-mail (preferir variáveis de ambiente)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', '')
    
    # Configurações de upload
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    BRANDING_UPLOAD_FOLDER = os.path.join(static_dir, 'uploads', 'branding')
    os.makedirs(BRANDING_UPLOAD_FOLDER, exist_ok=True)
    app.config['BRANDING_UPLOAD_FOLDER'] = BRANDING_UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    
    # ===========================================
    # INICIALIZAR EXTENSÕES
    # ===========================================
    db.init_app(app)
    mail.init_app(app)
    
    # ===========================================
    # ⚠️ PARTE CRÍTICA - IMPORTAR MODELS E CRIAR TABELAS
    # ===========================================
    with app.app_context():
        # Importar TODOS os models DENTRO do contexto
        # Isso força o SQLAlchemy a registrar as tabelas
        import logging as _logging
        _logger = _logging.getLogger(__name__)
        _logger.debug("Importando models...")
        from models import Cliente, Ordem, ItemServico, ItemPeca, Saida, ConfigContador, EnvioRelatorio, Profissional, OrdemStatusLog, OrdemAnexo, AuditoriaEvento
        _logger.debug("Models importados com sucesso!")
        # Criar todas as tabelas
        db.create_all()
        _logger.debug("Banco de dados inicializado com todas as tabelas!")

        # Migração leve para bancos SQLite já existentes (sem Alembic)
        inspector = inspect(db.engine)
        if 'ordens' in inspector.get_table_names():
            colunas_ordens = {c['name'] for c in inspector.get_columns('ordens')}
            if 'profissional_responsavel' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN profissional_responsavel VARCHAR(120)")
                )
                db.session.commit()
                _logger.info("Coluna profissional_responsavel adicionada em ordens")
            if 'forma_pagamento' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN forma_pagamento VARCHAR(30)")
                )
                db.session.commit()
                _logger.info("Coluna forma_pagamento adicionada em ordens")
            if 'observacao_interna' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN observacao_interna TEXT")
                )
                db.session.commit()
                _logger.info("Coluna observacao_interna adicionada em ordens")
            if 'debito_vencimento' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN debito_vencimento DATE")
                )
                db.session.commit()
                _logger.info("Coluna debito_vencimento adicionada em ordens")
            if 'debito_observacao' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN debito_observacao VARCHAR(255)")
                )
                db.session.commit()
                _logger.info("Coluna debito_observacao adicionada em ordens")
            if 'desconto_percentual' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN desconto_percentual FLOAT DEFAULT 0")
                )
                db.session.commit()
                _logger.info("Coluna desconto_percentual adicionada em ordens")
            if 'desconto_valor' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN desconto_valor FLOAT DEFAULT 0")
                )
                db.session.commit()
                _logger.info("Coluna desconto_valor adicionada em ordens")

        if 'servicos' in inspector.get_table_names():
            colunas_servicos = {c['name'] for c in inspector.get_columns('servicos')}
            if 'nome_profissional' not in colunas_servicos:
                db.session.execute(
                    text("ALTER TABLE servicos ADD COLUMN nome_profissional VARCHAR(120)")
                )
                db.session.commit()
                _logger.info("Coluna nome_profissional adicionada em servicos")

        if 'config_contador' in inspector.get_table_names():
            colunas_config = {c['name'] for c in inspector.get_columns('config_contador')}
            if 'profissional_envio_auto' not in colunas_config:
                db.session.execute(
                    text("ALTER TABLE config_contador ADD COLUMN profissional_envio_auto VARCHAR(120)")
                )
                db.session.commit()
                _logger.info("Coluna profissional_envio_auto adicionada em config_contador")
            novas_colunas_config = {
                'cep_provider_ativo': "ALTER TABLE config_contador ADD COLUMN cep_provider_ativo VARCHAR(60)",
                'cep_provider_primario': "ALTER TABLE config_contador ADD COLUMN cep_provider_primario VARCHAR(60)",
                'cep_api_key_primaria': "ALTER TABLE config_contador ADD COLUMN cep_api_key_primaria VARCHAR(255)",
                'cep_provider_secundario': "ALTER TABLE config_contador ADD COLUMN cep_provider_secundario VARCHAR(60)",
                'cep_api_key_secundaria': "ALTER TABLE config_contador ADD COLUMN cep_api_key_secundaria VARCHAR(255)",
                'placa_provider_ativo': "ALTER TABLE config_contador ADD COLUMN placa_provider_ativo VARCHAR(60)",
                'placa_provider_primario': "ALTER TABLE config_contador ADD COLUMN placa_provider_primario VARCHAR(60)",
                'placa_api_key_primaria': "ALTER TABLE config_contador ADD COLUMN placa_api_key_primaria VARCHAR(255)",
                'placa_provider_secundario': "ALTER TABLE config_contador ADD COLUMN placa_provider_secundario VARCHAR(60)",
                'placa_api_key_secundaria': "ALTER TABLE config_contador ADD COLUMN placa_api_key_secundaria VARCHAR(255)"
            }
            for nome_coluna, sql in novas_colunas_config.items():
                if nome_coluna not in colunas_config:
                    db.session.execute(text(sql))
                    db.session.commit()
                    _logger.info(f"Coluna {nome_coluna} adicionada em config_contador")

        if 'pecas' in inspector.get_table_names():
            colunas_pecas = {c['name'] for c in inspector.get_columns('pecas')}
            if 'valor_custo' not in colunas_pecas:
                db.session.execute(
                    text("ALTER TABLE pecas ADD COLUMN valor_custo FLOAT DEFAULT 0")
                )
                db.session.commit()
                _logger.info("Coluna valor_custo adicionada em pecas")
            if 'percentual_lucro' not in colunas_pecas:
                db.session.execute(
                    text("ALTER TABLE pecas ADD COLUMN percentual_lucro FLOAT DEFAULT 0")
                )
                db.session.commit()
                _logger.info("Coluna percentual_lucro adicionada em pecas")

        if 'config_contador' in inspector.get_table_names():
            colunas_config = {c['name'] for c in inspector.get_columns('config_contador')}
            if 'whatsapp_orcamento' not in colunas_config:
                db.session.execute(
                    text("ALTER TABLE config_contador ADD COLUMN whatsapp_orcamento VARCHAR(30)")
                )
                db.session.commit()
                _logger.info("Coluna whatsapp_orcamento adicionada em config_contador")
            novas_colunas_branding = {
                'nome_exibicao_sistema': "ALTER TABLE config_contador ADD COLUMN nome_exibicao_sistema VARCHAR(120)",
                'empresa_nome': "ALTER TABLE config_contador ADD COLUMN empresa_nome VARCHAR(120)",
                'empresa_email': "ALTER TABLE config_contador ADD COLUMN empresa_email VARCHAR(120)",
                'empresa_telefone': "ALTER TABLE config_contador ADD COLUMN empresa_telefone VARCHAR(30)",
                'empresa_endereco': "ALTER TABLE config_contador ADD COLUMN empresa_endereco VARCHAR(180)",
                'tema_visual': "ALTER TABLE config_contador ADD COLUMN tema_visual VARCHAR(20) DEFAULT 'escuro'",
                'logo_index_path': "ALTER TABLE config_contador ADD COLUMN logo_index_path VARCHAR(255)",
                'logo_index_formato': "ALTER TABLE config_contador ADD COLUMN logo_index_formato VARCHAR(20)",
                'logo_index_escala': "ALTER TABLE config_contador ADD COLUMN logo_index_escala FLOAT DEFAULT 1.0",
                'logo_index_offset_x': "ALTER TABLE config_contador ADD COLUMN logo_index_offset_x FLOAT DEFAULT 0.0",
                'logo_index_offset_y': "ALTER TABLE config_contador ADD COLUMN logo_index_offset_y FLOAT DEFAULT 0.0",
                'qrcode_1_path': "ALTER TABLE config_contador ADD COLUMN qrcode_1_path VARCHAR(255)",
                'qrcode_2_path': "ALTER TABLE config_contador ADD COLUMN qrcode_2_path VARCHAR(255)"
            }
            for nome_coluna, sql in novas_colunas_branding.items():
                if nome_coluna not in colunas_config:
                    db.session.execute(text(sql))
                    db.session.commit()
                    _logger.info(f"Coluna {nome_coluna} adicionada em config_contador")

        # Verificar quais tabelas foram criadas
        tabelas = inspector.get_table_names()
        _logger.debug(f"Tabelas criadas: {', '.join(tabelas)}")
    
    # ===========================================
    # REGISTRAR BLUEPRINTS (ROTAS)
    # ===========================================
    import logging as _logging2
    _logger2 = _logging2.getLogger(__name__)
    for bp in blueprints:
        app.register_blueprint(bp)
        _logger2.debug(f"Blueprint registrado: {bp.name}")
    
    # ===========================================
    # INICIAR SCHEDULER (TAREFAS AGENDADAS) - não iniciar em modo de teste
    # ===========================================
    if start_scheduler and not app.config.get('TESTING', False):
        if not scheduler.running:
            scheduler.start()
            atexit.register(lambda: scheduler.shutdown())
            _logger2.info("Agendador de tarefas iniciado!")

    def gerar_backup_diario():
        try:
            retencao_dias = int(os.environ.get('BACKUP_RETENTION_DAYS', '15'))
            info = criar_backup_database(prefixo='database_backup_', dias_retencao=retencao_dias)
            _logger2.info(f"Backup diario criado: {info['arquivo']}")
        except Exception as e:
            _logger2.exception(f"Backup diario falhou: {str(e)}")

    if start_scheduler and not app.config.get('TESTING', False):
        if not scheduler.get_job('daily_db_backup'):
            scheduler.add_job(
                gerar_backup_diario,
                trigger='cron',
                hour=2,
                minute=30,
                id='daily_db_backup',
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            _logger2.info("Job de backup diario agendado (02:30)")

    # Forçar exibição de erros no terminal por padrão, nível ajustável via env
    if os.environ.get('OFICINA39_USE_WEBVIEW') == '1':
        @app.after_request
        def desabilitar_cache_desktop(response):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response

    import logging
    log_level = os.environ.get('LOG_LEVEL', 'DEBUG').upper()
    logging.basicConfig(level=getattr(logging, log_level, logging.DEBUG))
    logger = logging.getLogger(__name__)
    
    return app

# ===========================================
# INICIAR O SERVIDOR
# ===========================================
if __name__ == '__main__':
    app = create_app()
    logger = __import__('logging').getLogger(__name__)
    logger.info("SISTEMA DE GESTAO DE OFICINA")
    logger.info("Banco de dados: database.db")
    logger.info("Acesse: http://localhost:5000")
    logger.info("E-mail: configuravel via banco")

    app.run(debug=True, host='0.0.0.0', port=5000)
