# ===========================================
# routes/ordens_routes.py - Rotas de Ordens de Serviço
# ===========================================

from flask import Blueprint, request, jsonify, send_file
from extensions import db
from datetime import datetime
import os
import uuid
import logging
from sqlalchemy import or_, func
from werkzeug.utils import secure_filename
from services.auditoria_service import registrar_evento_auditoria

ordens_bp = Blueprint('ordens', __name__, url_prefix='/api/ordens')
logger = logging.getLogger(__name__)

STATUS_CONCLUIDOS = {'Concluído', 'Garantia'}
FORMAS_PAGAMENTO_VALIDAS = {'Dinheiro', 'Pix', 'Cartão', 'Boleto', 'Transferência', 'Não informado'}
EXTENSOES_ANEXO = {'.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.xlsx', '.xls', '.txt'}


def _normalizar_forma_pagamento(valor):
    forma = (valor or '').strip()
    if not forma:
        return None
    mapping = {
        'dinheiro': 'Dinheiro',
        'pix': 'Pix',
        'cartao': 'Cartão',
        'cartão': 'Cartão',
        'boleto': 'Boleto',
        'transferencia': 'Transferência',
        'transferência': 'Transferência',
        'nao informado': 'Não informado',
        'não informado': 'Não informado'
    }
    return mapping.get(forma.lower(), forma)


def _registrar_log_status(ordem, status_anterior, status_novo, forma_pagamento=None, observacao=None):
    from models import OrdemStatusLog

    operador = (request.headers.get('X-Operador') or request.args.get('operador') or 'sistema').strip()[:80]
    origem = (request.headers.get('X-Origem') or 'api').strip()[:40]

    log = OrdemStatusLog(
        ordem_id=ordem.id,
        status_anterior=status_anterior,
        status_novo=status_novo,
        forma_pagamento=forma_pagamento,
        operador=operador or 'sistema',
        origem=origem or 'api',
        observacao=(observacao or '').strip()[:255] or None
    )
    db.session.add(log)


def _parse_data_iso(valor):
    if not valor:
        return None
    return datetime.strptime(valor, '%Y-%m-%d')


def _profissional_ativo_existe(nome_profissional):
    from models import Profissional
    nome = (nome_profissional or '').strip()
    if not nome:
        return False
    profissional = (
        Profissional.query
        .filter(func.lower(Profissional.nome) == nome.lower())
        .filter(Profissional.ativo.is_(True))
        .first()
    )
    return profissional is not None

# ===========================================
# LISTAR TODAS AS ORDENS
# ===========================================
@ordens_bp.route('/', methods=['GET'])
def listar_ordens():
    try:
        from models import Ordem
        ordens = Ordem.query.order_by(Ordem.id.desc()).all()
        return jsonify([o.to_dict() for o in ordens])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ===========================================
# BUSCAR ORDEM POR ID
# ===========================================
@ordens_bp.route('/<int:id>', methods=['GET'])
def buscar_ordem(id):
    try:
        from models import Ordem, Cliente
        ordem = Ordem.query.get(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404
        
        dados = ordem.to_dict()
        cliente = Cliente.query.get(ordem.cliente_id)
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
        from models import Ordem, ItemServico, ItemPeca, Cliente
        dados = request.json
        
        if not dados.get('cliente_id'):
            return jsonify({'erro': 'Cliente é obrigatório'}), 400
        
        cliente = Cliente.query.get(dados['cliente_id'])
        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        profissional_responsavel = (dados.get('profissional_responsavel') or '').strip()
        if not profissional_responsavel:
            return jsonify({'erro': 'Profissional responsável é obrigatório.'}), 400
        if not _profissional_ativo_existe(profissional_responsavel):
            return jsonify({'erro': 'Profissional responsável inválido. Selecione um profissional cadastrado e ativo.'}), 400
        
        ordem = Ordem(
            cliente_id=dados['cliente_id'],
            diagnostico=dados.get('diagnostico', ''),
            observacao_interna=dados.get('observacao_interna', ''),
            profissional_responsavel=profissional_responsavel,
            assinatura_cliente=dados.get('assinatura_cliente', ''),
            status='Aguardando',
            forma_pagamento=_normalizar_forma_pagamento(dados.get('forma_pagamento'))
        )
        
        db.session.add(ordem)
        db.session.flush()
        
        total_servicos = 0
        total_pecas = 0
        
        # Adicionar serviços
        for servico in dados.get('servicos', []):
            if servico.get('descricao_servico'):
                item = ItemServico(
                    ordem_id=ordem.id,
                    codigo_servico=servico.get('codigo_servico', ''),
                    descricao_servico=servico['descricao_servico'],
                    nome_profissional=(servico.get('nome_profissional') or ordem.profissional_responsavel or '').strip(),
                    valor_servico=servico.get('valor_servico', 0)
                )
                db.session.add(item)
                total_servicos += item.valor_servico
        
        # Adicionar peças
        for peca in dados.get('pecas', []):
            if peca.get('descricao_peca'):
                item = ItemPeca(
                    ordem_id=ordem.id,
                    codigo_peca=peca.get('codigo_peca', ''),
                    descricao_peca=peca['descricao_peca'],
                    quantidade=peca.get('quantidade', 1),
                    valor_unitario=peca.get('valor_unitario', 0)
                )
                db.session.add(item)
                total_pecas += item.quantidade * item.valor_unitario
        
        ordem.total_servicos = total_servicos
        ordem.total_pecas = total_pecas
        ordem.total_geral = total_servicos + total_pecas
        _registrar_log_status(ordem, None, ordem.status, forma_pagamento=ordem.forma_pagamento, observacao='Criação da ordem')
        
        db.session.commit()
        
        return jsonify(ordem.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# ATUALIZAR ORDEM (PUT)
# ===========================================
@ordens_bp.route('/<int:id>', methods=['PUT'])
def atualizar_ordem(id):
    try:
        from models import Ordem, ItemServico, ItemPeca
        ordem = Ordem.query.get(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404
        
        dados = request.json
        if ordem.status in STATUS_CONCLUIDOS and not bool(dados.get('forcar_edicao')):
            return jsonify({'erro': 'Ordem concluída está bloqueada para edição. Reabra a ordem para alterar.'}), 400
        
        total_geral_anterior = float(ordem.total_geral or 0)

        # Atualizar campos básicos
        if 'diagnostico' in dados:
            ordem.diagnostico = dados['diagnostico']
        if 'observacao_interna' in dados:
            ordem.observacao_interna = dados['observacao_interna']
        profissional_anterior = (ordem.profissional_responsavel or '').strip()
        if 'profissional_responsavel' in dados:
            novo_profissional = (dados.get('profissional_responsavel') or '').strip()
            if not novo_profissional:
                return jsonify({'erro': 'Profissional responsável é obrigatório.'}), 400
            if not _profissional_ativo_existe(novo_profissional):
                return jsonify({'erro': 'Profissional responsável inválido. Selecione um profissional cadastrado e ativo.'}), 400
            ordem.profissional_responsavel = novo_profissional
        if 'assinatura_cliente' in dados:
            ordem.assinatura_cliente = dados['assinatura_cliente']
        if 'status' in dados:
            ordem.status = dados['status']
        if 'forma_pagamento' in dados:
            ordem.forma_pagamento = _normalizar_forma_pagamento(dados.get('forma_pagamento'))
        
        # Atualizar serviços (remove antigos e adiciona novos)
        if 'servicos' in dados:
            ItemServico.query.filter_by(ordem_id=ordem.id).delete()
            for servico in dados['servicos']:
                if servico.get('descricao_servico'):
                    item = ItemServico(
                        ordem_id=ordem.id,
                        codigo_servico=servico.get('codigo_servico', ''),
                        descricao_servico=servico['descricao_servico'],
                        nome_profissional=(servico.get('nome_profissional') or ordem.profissional_responsavel or '').strip(),
                        valor_servico=servico.get('valor_servico', 0)
                    )
                    db.session.add(item)
        elif 'profissional_responsavel' in dados:
            # Se apenas o profissional foi alterado, propaga para todos os serviços da ordem.
            ItemServico.query.filter_by(ordem_id=ordem.id).update(
                {'nome_profissional': ordem.profissional_responsavel}
            )
        
        # Atualizar peças (remove antigas e adiciona novas)
        if 'pecas' in dados:
            ItemPeca.query.filter_by(ordem_id=ordem.id).delete()
            for peca in dados['pecas']:
                if peca.get('descricao_peca'):
                    item = ItemPeca(
                        ordem_id=ordem.id,
                        codigo_peca=peca.get('codigo_peca', ''),
                        descricao_peca=peca['descricao_peca'],
                        quantidade=peca.get('quantidade', 1),
                        valor_unitario=peca.get('valor_unitario', 0)
                    )
                    db.session.add(item)
        
        # Recalcular totais
        ordem.calcular_totais()
        total_geral_novo = float(ordem.total_geral or 0)
        if abs(total_geral_novo - total_geral_anterior) > 0.0001:
            registrar_evento_auditoria(
                acao='ALTERACAO_VALOR_OS',
                entidade='ordem',
                entidade_id=ordem.id,
                valor_anterior=f'{total_geral_anterior:.2f}',
                valor_novo=f'{total_geral_novo:.2f}',
                observacao='Valor total da OS alterado por edição.',
                request_ctx=request
            )
        db.session.commit()
        if 'profissional_responsavel' in dados and (ordem.profissional_responsavel or '').strip() != profissional_anterior:
            logger.info(
                "OS %s: profissional alterado de '%s' para '%s'",
                ordem.id,
                profissional_anterior or '---',
                (ordem.profissional_responsavel or '').strip() or '---'
            )
        
        return jsonify(ordem.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# ATUALIZAR STATUS DA ORDEM (PATCH)
# ===========================================
@ordens_bp.route('/<int:id>/status', methods=['PATCH'])
def atualizar_status(id):
    try:
        from models import Ordem
        ordem = Ordem.query.get(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404
        
        dados = request.json
        novo_status = dados.get('status')
        
        if not novo_status:
            return jsonify({'erro': 'Status não informado'}), 400
        
        status_validos = ['Aguardando', 'Aguardando peças', 'Em andamento', 'Concluído', 'Garantia']
        if novo_status not in status_validos:
            return jsonify({'erro': 'Status inválido'}), 400
        if novo_status in STATUS_CONCLUIDOS and not (ordem.profissional_responsavel or '').strip():
            return jsonify({'erro': 'Não é possível finalizar sem profissional responsável definido.'}), 400
        if novo_status in STATUS_CONCLUIDOS and not _profissional_ativo_existe(ordem.profissional_responsavel):
            return jsonify({'erro': 'Não é possível finalizar com profissional não cadastrado/ativo.'}), 400

        forma_pagamento = _normalizar_forma_pagamento(dados.get('forma_pagamento'))
        if forma_pagamento:
            if forma_pagamento not in FORMAS_PAGAMENTO_VALIDAS:
                return jsonify({'erro': 'Forma de pagamento inválida'}), 400

        status_anterior = ordem.status
        ordem.status = novo_status
        if forma_pagamento:
            ordem.forma_pagamento = forma_pagamento

        # Salvar data de conclusão se for Concluído ou Garantia
        if novo_status in STATUS_CONCLUIDOS:
            if dados.get('data_conclusao'):
                try:
                    data_str = dados['data_conclusao'].replace('Z', '+00:00')
                    ordem.data_conclusao = datetime.fromisoformat(data_str)
                except:
                    ordem.data_conclusao = datetime.now()
            else:
                ordem.data_conclusao = datetime.now()

        _registrar_log_status(
            ordem,
            status_anterior=status_anterior,
            status_novo=novo_status,
            forma_pagamento=ordem.forma_pagamento,
            observacao=(dados.get('observacao') or '').strip() or None
        )
        db.session.commit()
        logger.info(
            "OS %s: status alterado de '%s' para '%s' (forma_pagamento=%s)",
            ordem.id,
            status_anterior or '---',
            novo_status,
            ordem.forma_pagamento or '---'
        )
        
        return jsonify({'mensagem': 'Status atualizado', 'status': novo_status, 'forma_pagamento': ordem.forma_pagamento})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

# ===========================================
# DELETAR ORDEM
# ===========================================
@ordens_bp.route('/<int:id>', methods=['DELETE'])
def deletar_ordem(id):
    try:
        from models import Ordem
        ordem = Ordem.query.get(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404
        
        registrar_evento_auditoria(
            acao='EXCLUSAO_OS',
            entidade='ordem',
            entidade_id=ordem.id,
            valor_anterior=f'{float(ordem.total_geral or 0):.2f}',
            valor_novo='0.00',
            observacao='OS removida.',
            request_ctx=request
        )
        db.session.delete(ordem)
        db.session.commit()
        return jsonify({'mensagem': 'Ordem removida com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/reabrir', methods=['POST'])
def reabrir_ordem(id):
    try:
        from models import Ordem
        ordem = Ordem.query.get(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404

        if ordem.status not in STATUS_CONCLUIDOS:
            return jsonify({'erro': 'Somente ordens concluídas ou em garantia podem ser reabertas.'}), 400

        status_anterior = ordem.status
        ordem.status = 'Em andamento'
        _registrar_log_status(
            ordem,
            status_anterior=status_anterior,
            status_novo='Em andamento',
            forma_pagamento=ordem.forma_pagamento,
            observacao='Reabertura da ordem'
        )
        registrar_evento_auditoria(
            acao='REABERTURA_OS',
            entidade='ordem',
            entidade_id=ordem.id,
            valor_anterior=status_anterior,
            valor_novo='Em andamento',
            observacao='Ordem reaberta para edição.',
            request_ctx=request
        )
        db.session.commit()
        return jsonify({'mensagem': 'Ordem reaberta com sucesso.', 'status': ordem.status})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/status-log', methods=['GET'])
def listar_log_status(id):
    try:
        from models import Ordem, OrdemStatusLog
        ordem = Ordem.query.get(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404

        logs = OrdemStatusLog.query.filter_by(ordem_id=id).order_by(OrdemStatusLog.data_evento.desc()).all()
        return jsonify([log.to_dict() for log in logs])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/duplicar', methods=['POST'])
def duplicar_ordem(id):
    try:
        from models import Ordem, ItemServico, ItemPeca
        origem = Ordem.query.get(id)
        if not origem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404

        nova = Ordem(
            cliente_id=origem.cliente_id,
            diagnostico=origem.diagnostico or '',
            observacao_interna=origem.observacao_interna or '',
            profissional_responsavel=origem.profissional_responsavel or '',
            assinatura_cliente='',
            status='Aguardando',
            forma_pagamento=None
        )
        db.session.add(nova)
        db.session.flush()

        total_servicos = 0.0
        total_pecas = 0.0

        for s in origem.servicos:
            novo_serv = ItemServico(
                ordem_id=nova.id,
                codigo_servico=s.codigo_servico,
                descricao_servico=s.descricao_servico,
                nome_profissional=s.nome_profissional or nova.profissional_responsavel or '',
                valor_servico=s.valor_servico or 0
            )
            db.session.add(novo_serv)
            total_servicos += float(novo_serv.valor_servico or 0)

        for p in origem.pecas:
            nova_peca = ItemPeca(
                ordem_id=nova.id,
                codigo_peca=p.codigo_peca,
                descricao_peca=p.descricao_peca,
                quantidade=p.quantidade or 0,
                valor_unitario=p.valor_unitario or 0
            )
            db.session.add(nova_peca)
            total_pecas += float((nova_peca.quantidade or 0) * (nova_peca.valor_unitario or 0))

        nova.total_servicos = total_servicos
        nova.total_pecas = total_pecas
        nova.total_geral = total_servicos + total_pecas

        _registrar_log_status(nova, None, nova.status, observacao=f'Duplicada da OS #{origem.id}')
        db.session.commit()
        return jsonify({'mensagem': 'Ordem duplicada com sucesso.', 'nova_ordem_id': nova.id, 'ordem': nova.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/anexos', methods=['GET'])
def listar_anexos(id):
    try:
        from models import Ordem, OrdemAnexo
        ordem = Ordem.query.get(id)
        if not ordem:
            return jsonify({'erro': 'Ordem não encontrada'}), 404
        anexos = OrdemAnexo.query.filter_by(ordem_id=id).order_by(OrdemAnexo.created_at.desc()).all()
        return jsonify([a.to_dict() for a in anexos])
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@ordens_bp.route('/<int:id>/anexos', methods=['POST'])
def upload_anexo(id):
    try:
        from models import Ordem, OrdemAnexo
        ordem = Ordem.query.get(id)
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
        from models import OrdemAnexo
        anexo = OrdemAnexo.query.filter_by(id=anexo_id, ordem_id=id).first()
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
        from models import OrdemAnexo
        anexo = OrdemAnexo.query.filter_by(id=anexo_id, ordem_id=id).first()
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
        from models import Ordem, Cliente
        cliente = request.args.get('cliente', '')
        status = request.args.get('status', '')
        profissional = request.args.get('profissional', '')
        forma_pagamento = request.args.get('forma_pagamento', '')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        
        query = Ordem.query
        
        if cliente:
            termo = cliente.strip()
            termo_numerico = ''.join(ch for ch in termo if ch.isdigit())
            cpf_sem_mascara = func.replace(func.replace(func.replace(Cliente.cpf, '.', ''), '-', ''), '/', '')

            condicoes = [
                Cliente.nome_cliente.ilike(f'%{termo}%'),
                Cliente.cpf.ilike(f'%{termo}%')
            ]
            if termo_numerico:
                condicoes.append(cpf_sem_mascara.ilike(f'%{termo_numerico}%'))

            clientes = Cliente.query.filter(or_(*condicoes)).all()
            ids_clientes = [c.id for c in clientes]
            if ids_clientes:
                query = query.filter(Ordem.cliente_id.in_(ids_clientes))
            else:
                return jsonify([])
        
        if status:
            query = query.filter(Ordem.status == status)
        if profissional:
            query = query.filter(Ordem.profissional_responsavel.ilike(f'%{profissional}%'))
        if forma_pagamento:
            query = query.filter(Ordem.forma_pagamento == forma_pagamento)
        if data_inicio:
            dt_inicio = _parse_data_iso(data_inicio)
            query = query.filter(Ordem.data_entrada >= dt_inicio)
        if data_fim:
            dt_fim = _parse_data_iso(data_fim).replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(Ordem.data_entrada <= dt_fim)
        
        ordens = query.order_by(Ordem.id.desc()).all()
        return jsonify([o.to_dict() for o in ordens])
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
