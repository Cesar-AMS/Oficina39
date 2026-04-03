from flask import Blueprint, jsonify, request, send_file

from services.anexo_service import excluir_anexo, listar_anexos, obter_anexo, resolver_caminho_absoluto, salvar_anexo


anexos_bp = Blueprint('anexos', __name__, url_prefix='/api/anexos')


@anexos_bp.route('/', methods=['GET'])
def listar_anexos_genericos():
    try:
        entidade_tipo = request.args.get('entidade_tipo')
        entidade_id = request.args.get('entidade_id')
        anexos = listar_anexos(entidade_tipo, entidade_id)
        return jsonify([anexo.to_dict() for anexo in anexos])
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@anexos_bp.route('/', methods=['POST'])
def upload_anexo_generico():
    try:
        entidade_tipo = request.form.get('entidade_tipo')
        entidade_id = request.form.get('entidade_id')
        descricao = request.form.get('descricao')
        categoria = request.form.get('categoria', 'documento')
        arquivo = request.files.get('arquivo')
        anexo = salvar_anexo(entidade_tipo, entidade_id, arquivo, descricao=descricao, categoria=categoria)
        return jsonify(anexo.to_dict()), 201
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@anexos_bp.route('/<int:anexo_id>/download', methods=['GET'])
def download_anexo_generico(anexo_id):
    try:
        entidade_tipo = request.args.get('entidade_tipo')
        entidade_id = request.args.get('entidade_id')
        anexo = obter_anexo(entidade_tipo, entidade_id, anexo_id)
        if not anexo:
            return jsonify({'erro': 'Anexo não encontrado.'}), 404
        caminho_abs = resolver_caminho_absoluto(anexo)
        return send_file(caminho_abs, as_attachment=True, download_name=getattr(anexo, 'nome_arquivo', None) or getattr(anexo, 'nome_original', 'anexo'))
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@anexos_bp.route('/<int:anexo_id>', methods=['DELETE'])
def excluir_anexo_generico(anexo_id):
    try:
        entidade_tipo = request.args.get('entidade_tipo')
        entidade_id = request.args.get('entidade_id')
        excluir_anexo(entidade_tipo, entidade_id, anexo_id)
        return jsonify({'mensagem': 'Anexo removido com sucesso.'})
    except LookupError as e:
        return jsonify({'erro': str(e)}), 404
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
