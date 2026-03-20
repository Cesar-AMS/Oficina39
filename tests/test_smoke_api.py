import unittest
from datetime import datetime

from app import create_app


class SmokeApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_pagina_inicial(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_pagina_consultar_os(self):
        resp = self.client.get("/consultarOS.html")
        self.assertEqual(resp.status_code, 200)

    def test_pagina_relatorio_profissionais(self):
        resp = self.client.get("/relatorios/producao-profissionais")
        self.assertEqual(resp.status_code, 200)

    def test_api_ordens_lista(self):
        resp = self.client.get("/api/ordens/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), list)

    def test_api_ordens_busca_cliente_ou_cpf(self):
        resp = self.client.get("/api/ordens/busca?cliente=teste")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), list)

    def test_api_config_contador(self):
        resp = self.client.get("/api/config/contador")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), dict)

    def test_api_producao_profissionais(self):
        resp = self.client.get("/api/relatorios/producao-profissionais")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), list)

    def test_api_operacional_servicos_pecas_saidas(self):
        resp = self.client.get("/api/relatorios/operacional-servicos-pecas-saidas")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), dict)

    def test_api_fluxo_periodo_dia(self):
        resp = self.client.get("/api/fluxo/periodo?periodo=dia")
        self.assertEqual(resp.status_code, 200)
        dados = resp.get_json()
        self.assertIsInstance(dados, dict)
        self.assertIn("entradas", dados)
        self.assertIn("saidas", dados)

    def test_api_fluxo_cria_e_remove_saida(self):
        descricao = f"Teste smoke {datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        payload = {
            "descricao": descricao,
            "valor": 12.34,
            "categoria": "Outros"
        }
        criar = self.client.post("/api/fluxo/saidas", json=payload)
        self.assertEqual(criar.status_code, 201)
        dados_criacao = criar.get_json()
        self.assertIsInstance(dados_criacao, dict)
        self.assertEqual(dados_criacao["descricao"], descricao)

        excluir = self.client.delete(f"/api/fluxo/saidas/{dados_criacao['id']}")
        self.assertEqual(excluir.status_code, 200)


if __name__ == "__main__":
    unittest.main()
