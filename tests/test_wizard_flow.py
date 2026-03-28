import os
from app import create_app
from extensions import db


def test_wizard_draft_and_final_save():
    # Ensure testing mode
    os.environ['TESTING'] = '1'
    app = create_app(testing=True)

    client = app.test_client()

    # 1) Save a draft (step-by-step form would save progressively)
    draft_payload = {
        'placa': 'ABC-1234',
        'nome_cliente': 'Cliente Teste Draft',
        'telefone': '11999990000'
    }

    resp = client.post('/api/clientes/draft', json=draft_payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'id' in data
    draft_id = data['id']
    assert data.get('placa') == 'ABC-1234'

    # 2) Now perform the final save (full create) using required fields
    final_payload = {
        'nome_cliente': 'Cliente Teste Draft',
        'cpf': '12345678901',
        'telefone': '11999990000',
        'placa': 'ABC-1234'
    }

    resp2 = client.post('/api/clientes/', json=final_payload)
    assert resp2.status_code == 201
    cliente = resp2.get_json()
    assert cliente.get('nome_cliente') == 'Cliente Teste Draft'
    assert cliente.get('cpf') == '12345678901'

    # 3) Ensure the ClienteDraft row still exists (drafts are separate)
    with app.app_context():
        from models import ClienteDraft
        d = db.session.get(ClienteDraft, draft_id)
        assert d is not None
        assert d.placa == 'ABC-1234'
