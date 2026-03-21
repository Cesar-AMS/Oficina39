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
def create_app():
    # Caminho absoluto para a pasta static
    basedir = os.path.abspath(os.path.dirname(__file__))
    static_dir = os.path.join(basedir, 'static')
    
    views_dir = os.path.join(basedir, 'views')

    # Criar app com pasta estática configurada
    app = Flask(__name__, 
                template_folder=views_dir,
                static_folder=static_dir,
                static_url_path='/static')
    
    # Configurações
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configurações de e-mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = ''
    app.config['MAIL_PASSWORD'] = ''
    app.config['MAIL_DEFAULT_SENDER'] = ''
    
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
        print("Importando models...")
        from models import Cliente, Ordem, ItemServico, ItemPeca, Saida, ConfigContador, EnvioRelatorio, Profissional, OrdemStatusLog, OrdemAnexo, AuditoriaEvento
        print("Models importados com sucesso!")
        
        # Criar todas as tabelas
        db.create_all()
        print("Banco de dados inicializado com todas as tabelas!")

        # Migração leve para bancos SQLite já existentes (sem Alembic)
        inspector = inspect(db.engine)
        if 'ordens' in inspector.get_table_names():
            colunas_ordens = {c['name'] for c in inspector.get_columns('ordens')}
            if 'profissional_responsavel' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN profissional_responsavel VARCHAR(120)")
                )
                db.session.commit()
                print("Coluna profissional_responsavel adicionada em ordens")
            if 'forma_pagamento' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN forma_pagamento VARCHAR(30)")
                )
                db.session.commit()
                print("Coluna forma_pagamento adicionada em ordens")
            if 'observacao_interna' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN observacao_interna TEXT")
                )
                db.session.commit()
                print("Coluna observacao_interna adicionada em ordens")
            if 'debito_vencimento' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN debito_vencimento DATE")
                )
                db.session.commit()
                print("Coluna debito_vencimento adicionada em ordens")
            if 'debito_observacao' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN debito_observacao VARCHAR(255)")
                )
                db.session.commit()
                print("Coluna debito_observacao adicionada em ordens")
            if 'desconto_percentual' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN desconto_percentual FLOAT DEFAULT 0")
                )
                db.session.commit()
                print("Coluna desconto_percentual adicionada em ordens")
            if 'desconto_valor' not in colunas_ordens:
                db.session.execute(
                    text("ALTER TABLE ordens ADD COLUMN desconto_valor FLOAT DEFAULT 0")
                )
                db.session.commit()
                print("Coluna desconto_valor adicionada em ordens")

        if 'servicos' in inspector.get_table_names():
            colunas_servicos = {c['name'] for c in inspector.get_columns('servicos')}
            if 'nome_profissional' not in colunas_servicos:
                db.session.execute(
                    text("ALTER TABLE servicos ADD COLUMN nome_profissional VARCHAR(120)")
                )
                db.session.commit()
                print("Coluna nome_profissional adicionada em servicos")

        if 'config_contador' in inspector.get_table_names():
            colunas_config = {c['name'] for c in inspector.get_columns('config_contador')}
            if 'profissional_envio_auto' not in colunas_config:
                db.session.execute(
                    text("ALTER TABLE config_contador ADD COLUMN profissional_envio_auto VARCHAR(120)")
                )
                db.session.commit()
                print("Coluna profissional_envio_auto adicionada em config_contador")
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
                    print(f"Coluna {nome_coluna} adicionada em config_contador")

        if 'pecas' in inspector.get_table_names():
            colunas_pecas = {c['name'] for c in inspector.get_columns('pecas')}
            if 'valor_custo' not in colunas_pecas:
                db.session.execute(
                    text("ALTER TABLE pecas ADD COLUMN valor_custo FLOAT DEFAULT 0")
                )
                db.session.commit()
                print("Coluna valor_custo adicionada em pecas")
            if 'percentual_lucro' not in colunas_pecas:
                db.session.execute(
                    text("ALTER TABLE pecas ADD COLUMN percentual_lucro FLOAT DEFAULT 0")
                )
                db.session.commit()
                print("Coluna percentual_lucro adicionada em pecas")

        if 'config_contador' in inspector.get_table_names():
            colunas_config = {c['name'] for c in inspector.get_columns('config_contador')}
            if 'whatsapp_orcamento' not in colunas_config:
                db.session.execute(
                    text("ALTER TABLE config_contador ADD COLUMN whatsapp_orcamento VARCHAR(30)")
                )
                db.session.commit()
                print("Coluna whatsapp_orcamento adicionada em config_contador")
            novas_colunas_branding = {
                'nome_exibicao_sistema': "ALTER TABLE config_contador ADD COLUMN nome_exibicao_sistema VARCHAR(120)",
                'empresa_nome': "ALTER TABLE config_contador ADD COLUMN empresa_nome VARCHAR(120)",
                'empresa_email': "ALTER TABLE config_contador ADD COLUMN empresa_email VARCHAR(120)",
                'empresa_telefone': "ALTER TABLE config_contador ADD COLUMN empresa_telefone VARCHAR(30)",
                'empresa_endereco': "ALTER TABLE config_contador ADD COLUMN empresa_endereco VARCHAR(180)",
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
                    print(f"Coluna {nome_coluna} adicionada em config_contador")

        # Verificar quais tabelas foram criadas
        tabelas = inspector.get_table_names()
        print(f"Tabelas criadas: {', '.join(tabelas)}")
    
    # ===========================================
    # REGISTRAR BLUEPRINTS (ROTAS)
    # ===========================================
    for bp in blueprints:
        app.register_blueprint(bp)
        print(f"Blueprint registrado: {bp.name}")
    
    # ===========================================
    # INICIAR SCHEDULER (TAREFAS AGENDADAS)
    # ===========================================
    if not scheduler.running:
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())
        print("Agendador de tarefas iniciado!")

    def gerar_backup_diario():
        try:
            retencao_dias = int(os.environ.get('BACKUP_RETENTION_DAYS', '15'))
            info = criar_backup_database(prefixo='database_backup_', dias_retencao=retencao_dias)
            print(f"Backup diario criado: {info['arquivo']}")
        except Exception as e:
            print(f"Backup diario falhou: {str(e)}")

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
        print("Job de backup diario agendado (02:30)")

    # Forçar exibição de erros no terminal
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    return app

# ===========================================
# INICIAR O SERVIDOR
# ===========================================
if __name__ == '__main__':
    app = create_app()
    
    print("=" * 50)
    print("SISTEMA DE GESTAO DE OFICINA")
    print("=" * 50)
    print("Banco de dados: database.db")
    print("Acesse: http://localhost:5000")
    print("E-mail: configuravel via banco")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
