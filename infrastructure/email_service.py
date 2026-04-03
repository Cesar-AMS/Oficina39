# ===========================================
# services/email_service.py - Serviço de E-mail
# ===========================================

from flask_mail import Message
from extensions import mail
from models import EnvioRelatorio
from extensions import db
from datetime import datetime
from services.comunicacao_service import enviar_email_imediato

def enviar_relatorio_email(remetente, senha, destinatario, periodo, html, formato='html'):
    """
    Envia e-mail com relatório e registra no histórico
    
    Args:
        remetente: E-mail do remetente (cliente)
        senha: Senha de app do Gmail
        destinatario: E-mail do destinatário (contador)
        periodo: Período do relatório
        html: Conteúdo HTML do relatório
        formato: Formato do relatório (html, csv, xlsx, pdf)
    
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        comunicacao = enviar_email_imediato(
            destino=destinatario,
            assunto=f"Relatório Fluxo de Caixa - {periodo}",
            mensagem=html,
            entidade_tipo='relatorio',
            remetente=remetente,
            senha=senha,
            html=True,
        )
        if comunicacao.status != 'enviado':
            raise RuntimeError(comunicacao.erro or 'Falha ao enviar e-mail.')
        
        # Registrar sucesso
        registro = EnvioRelatorio(
            periodo=periodo,
            formato=formato,
            remetente=remetente,
            destinatario=destinatario,
            status='enviado',
            data_envio=datetime.now()
        )
        db.session.add(registro)
        db.session.commit()
        
        return True, "E-mail enviado com sucesso"
        
    except Exception as e:
        # Registrar erro
        registro = EnvioRelatorio(
            periodo=periodo,
            formato=formato,
            remetente=remetente,
            destinatario=destinatario,
            status='erro',
            erro_msg=str(e),
            data_envio=datetime.now()
        )
        db.session.add(registro)
        db.session.commit()
        
        return False, str(e)


def testar_conexao_email(remetente, senha):
    """
    Testa se as credenciais de e-mail são válidas
    
    Args:
        remetente: E-mail do remetente
        senha: Senha de app do Gmail
    
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        mail.username = remetente
        mail.password = senha
        mail.sender = remetente
        mail.extract_config()
        with mail.connect():
            pass
        
        return True, "Conexão bem sucedida"
        
    except Exception as e:
        return False, str(e)
