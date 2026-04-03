import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import Anexo
from repositories.anexo_repository import anexo_repository


EXTENSOES_ANEXO = {'.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.xlsx', '.xls', '.txt', '.webp'}
ENTIDADES_ANEXO = {'ordem', 'cliente', 'profissional', 'peca', 'servico', 'pagamento'}


def listar_anexos(entidade_tipo, entidade_id):
    return anexo_repository.listar_por_entidade(entidade_tipo, entidade_id, incluir_legado=True)


def obter_anexo(entidade_tipo, entidade_id, anexo_id):
    return anexo_repository.obter_por_entidade(entidade_tipo, entidade_id, anexo_id, incluir_legado=True)


def salvar_anexo(entidade_tipo, entidade_id, arquivo, descricao=None, categoria='documento', usuario_id=None):
    entidade = _validar_entidade(entidade_tipo)
    entidade_id_int = _validar_entidade_id(entidade_id)

    if not arquivo or not getattr(arquivo, 'filename', None):
        raise ValueError('Arquivo não enviado.')

    nome_original = arquivo.filename
    nome_seguro = secure_filename(nome_original)
    ext = os.path.splitext(nome_seguro)[1].lower()
    if ext not in EXTENSOES_ANEXO:
        raise ValueError('Tipo de arquivo não permitido.')

    base_dir = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.root_path, 'uploads')
    pasta_rel = os.path.join('anexos', entidade, str(entidade_id_int))
    pasta_abs = os.path.join(base_dir, pasta_rel)
    os.makedirs(pasta_abs, exist_ok=True)

    nome_final = f'{uuid.uuid4().hex}{ext}'
    caminho_abs = os.path.join(pasta_abs, nome_final)
    arquivo.save(caminho_abs)

    caminho_rel = os.path.join(pasta_rel, nome_final).replace('\\', '/')
    anexo = Anexo(
        entidade_tipo=entidade,
        entidade_id=entidade_id_int,
        nome_arquivo=nome_original,
        caminho_arquivo=caminho_rel,
        tamanho_bytes=os.path.getsize(caminho_abs),
        mime_type=(getattr(arquivo, 'mimetype', None) or '').strip() or None,
        descricao=(descricao or '').strip()[:200] or None,
        categoria=(categoria or 'documento').strip()[:50] or 'documento',
        usuario_id=usuario_id,
        metadata_json={},
    )
    anexo_repository.criar(anexo)
    db.session.commit()
    return anexo


def excluir_anexo(entidade_tipo, entidade_id, anexo_id):
    anexo = obter_anexo(entidade_tipo, entidade_id, anexo_id)
    if not anexo:
        raise LookupError('Anexo não encontrado.')

    caminho_abs = resolver_caminho_absoluto(anexo)
    if os.path.exists(caminho_abs):
        try:
            os.remove(caminho_abs)
        except Exception:
            pass

    if isinstance(anexo, Anexo):
        anexo_repository.excluir(anexo)
    else:
        db.session.delete(anexo)
    db.session.commit()
    return True


def resolver_caminho_absoluto(anexo):
    upload_folder = current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.root_path, 'uploads')
    caminho_rel = getattr(anexo, 'caminho_arquivo', None) or getattr(anexo, 'caminho_relativo', None)
    if not caminho_rel:
        raise FileNotFoundError('Caminho do anexo não encontrado.')
    return os.path.join(upload_folder, caminho_rel.replace('/', os.sep))


def _validar_entidade(entidade_tipo):
    entidade = (entidade_tipo or '').strip().lower()
    if entidade not in ENTIDADES_ANEXO:
        raise ValueError('Entidade de anexo inválida.')
    return entidade


def _validar_entidade_id(entidade_id):
    try:
        return int(entidade_id)
    except (TypeError, ValueError):
        raise ValueError('Entidade do anexo não informada.')
