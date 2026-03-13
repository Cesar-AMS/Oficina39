# ===========================================
# extensions.py - Extensões do Flask
# ===========================================

import importlib.metadata

from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask import current_app


_original_version = importlib.metadata.version


def _safe_package_version(name):
    valor = _original_version(name)
    if name == 'APScheduler' and valor is None:
        return '3.10.4'
    return valor


importlib.metadata.version = _safe_package_version

from apscheduler.schedulers.background import BackgroundScheduler

# Inicializa as extensões (sem app ainda)
db = SQLAlchemy()
mail = Mail()
scheduler = BackgroundScheduler()

# ===========================================
# FUNÇÃO PARA ACESSAR O DB NO CONTEXTO DA APP
# ===========================================

def get_db():
    """
    Retorna a instância do SQLAlchemy dentro do contexto da aplicação.
    """
    # O próprio db já é a instância correta
    return db

# ===========================================
# FUNÇÃO PARA INICIALIZAR AS EXTENSÕES COM A APP
# ===========================================

def init_extensions(app):
    """Inicializa todas as extensões com a aplicação Flask"""
    db.init_app(app)
    mail.init_app(app)
    
    # Configurar scheduler se necessário
    if not scheduler.running:
        scheduler.start()
    
    print("✅ Extensões inicializadas com sucesso!")

# ===========================================
# FUNÇÃO PARA FECHAR CONEXÕES (OPCIONAL)
# ===========================================

def close_scheduler():
    """Fecha o scheduler quando a aplicação for encerrada"""
    if scheduler.running:
        scheduler.shutdown()
        print("✅ Scheduler encerrado")
