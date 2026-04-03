from __future__ import annotations

import io

from flask import Blueprint, jsonify, request, send_file

from .auth_utils import require_auth
from services.orcamento_pdf_service import gerar_pdf_preview
from services.order_pdf_service import suggested_preview_pdf_name


orcamento_preview_bp = Blueprint('orcamento_preview', __name__, url_prefix='/api/orcamento')


@orcamento_preview_bp.route('/preview', methods=['POST'])
@require_auth
def preview_orcamento():
    try:
        pdf_bytes = gerar_pdf_preview(request.get_json() or {})
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=False,
            download_name=suggested_preview_pdf_name(),
        )
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
    except LookupError as e:
        return jsonify({'erro': str(e)}), 404
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
