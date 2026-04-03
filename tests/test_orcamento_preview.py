import os
os.environ['TESTING'] = '1'

import unittest
from datetime import datetime

from app import create_app
from extensions import db
from models import Cliente, Ordem, Profissional


class OrcamentoPreviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(testing=True)
        cls.client = cls.app.test_client()

    def _login_admin(self):
        resp = self.client.post("/api/auth/login", json={
            "email": "admin@oficina39.local",
            "senha": "admin123",
        })
        self.assertEqual(resp.status_code, 200)
        return resp.get_json()["token"]

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self._login_admin()}"}

    def _cliente_id(self):
        with self.app.app_context():
            sufixo = datetime.now().strftime('%H%M%S%f')
            cliente = Cliente(
                nome_cliente=f"Cliente Preview {sufixo}",
                cpf=f"52998{sufixo[:6]}",
                telefone="11999998888",
                email=f"preview{sufixo}@teste.local",
            )
            db.session.add(cliente)
            db.session.commit()
            return cliente.id

    def _profissional_nome(self):
        with self.app.app_context():
            profissional = Profissional.query.filter_by(ativo=True).first()
            if profissional:
                return profissional.nome
            profissional = Profissional(nome="Prof Preview", cnpj="12345678000199", ativo=True)
            db.session.add(profissional)
            db.session.commit()
            return profissional.nome

    def test_preview_gera_pdf_sem_salvar_os(self):
        cliente_id = self._cliente_id()
        profissional = self._profissional_nome()
        with self.app.app_context():
            antes = Ordem.query.count()

        resp = self.client.post("/api/orcamento/preview", json={
            "cliente_id": cliente_id,
            "profissional_responsavel": profissional,
            "diagnostico": "Preview sem salvar",
            "servicos": [{"descricao_servico": "Teste", "valor_servico": 90}],
        }, headers=self._auth_headers())

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data.startswith(b"%PDF"))
        with self.app.app_context():
            depois = Ordem.query.count()
        self.assertEqual(antes, depois)

    def test_preview_valida_campos_obrigatorios(self):
        resp = self.client.post("/api/orcamento/preview", json={
            "diagnostico": "Sem cliente",
            "servicos": [],
            "pecas": [],
        }, headers=self._auth_headers())

        self.assertEqual(resp.status_code, 400)
        self.assertIn("erro", resp.get_json())

    def test_preview_com_dados_completos_retorna_pdf(self):
        cliente_id = self._cliente_id()
        profissional = self._profissional_nome()
        resp = self.client.post("/api/orcamento/preview", json={
            "cliente_id": cliente_id,
            "profissional_responsavel": profissional,
            "diagnostico": "Orcamento completo",
            "servicos": [{"descricao_servico": "Servico A", "valor_servico": 100}],
            "pecas": [{"descricao_peca": "Peca A", "quantidade": 2, "valor_unitario": 15}],
        }, headers=self._auth_headers())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/pdf")
        self.assertTrue(resp.data.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
