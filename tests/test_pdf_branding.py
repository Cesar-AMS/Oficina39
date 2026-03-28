import os

from app import create_app
from extensions import db
from models import Cliente, ConfigContador, Ordem
from controllers.export_routes import _obter_branding_empresa


def test_branding_resolve_logo_personalizada_com_caminho_publico_mesmo_fora_da_raiz():
    os.environ['TESTING'] = '1'
    app = create_app(testing=True)

    with app.app_context():
        cliente = Cliente(nome_cliente='Cliente PDF', cpf='12345678900')
        db.session.add(cliente)
        db.session.flush()

        ordem = Ordem(cliente_id=cliente.id, diagnostico='Teste PDF branding')
        db.session.add(ordem)

        config = ConfigContador(
            logo_index_path='/static/uploads/branding/test_logo_placeholder.png'
        )
        db.session.add(config)
        db.session.commit()

    diretorio_original = os.getcwd()
    diretorio_alternativo = os.path.dirname(diretorio_original)

    try:
        os.chdir(diretorio_alternativo)
        with app.app_context():
            branding = _obter_branding_empresa()
    finally:
        os.chdir(diretorio_original)

    assert branding['logo_path']
    assert branding['logo_path'].endswith(
        os.path.join('static', 'uploads', 'branding', 'test_logo_placeholder.png')
    )
