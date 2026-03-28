import os
from app import create_app
from extensions import db


def test_promote_draft_to_cliente():
    os.environ['TESTING'] = '1'
    app = create_app(testing=True)
    client = app.test_client()

    # create draft
    draft_payload = {
        'placa': 'XYZ-9999',
        'nome_cliente': 'Promo Draft',
        'telefone': '11911112222'
    }
    resp = client.post('/api/clientes/draft', json=draft_payload)
    assert resp.status_code == 200
    draft = resp.get_json()
    draft_id = draft['id']

    # promote using draft_id
    final_payload = {
        'draft_id': draft_id,
        # cpf is required for final save; we'll add it
        'cpf': '98765432100'
    }
    resp2 = client.post('/api/clientes/', json=final_payload)
    assert resp2.status_code == 201
    cliente = resp2.get_json()
    assert cliente['placa'] == 'XYZ-9999'
    assert cliente['cpf'] == '98765432100'

    # ensure draft deleted
    with app.app_context():
        from models import ClienteDraft
        d = db.session.get(ClienteDraft, draft_id)
        assert d is None
