import os
os.environ['TESTING'] = '1'

import unittest
from datetime import datetime

from app import create_app
from extensions import db
from models import Cliente, MovimentoCaixa, Profissional


class SmokeApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(testing=True)
        cls.client = cls.app.test_client()

    def _criar_cliente_teste(self):
        with self.app.app_context():
            cliente = Cliente(
                nome_cliente=f"Cliente Teste {datetime.now().strftime('%H%M%S%f')}",
                cpf=f"999{datetime.now().strftime('%H%M%S%f')[:8]}"
            )
            db.session.add(cliente)
            db.session.commit()
            return cliente.id

    def _obter_profissional_ativo(self):
        with self.app.app_context():
            profissional = Profissional.query.filter_by(ativo=True).first()
            if profissional:
                return profissional.nome

            profissional = Profissional(
                nome=f"Profissional Teste {datetime.now().strftime('%H%M%S')}",
                cnpj=f"{datetime.now().strftime('%Y%m%d%H%M%S')}",
                ativo=True
            )
            db.session.add(profissional)
            db.session.commit()
            return profissional.nome

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

    def test_api_servicos_crud(self):
        nome_base = f"Servico Teste {datetime.now().strftime('%H%M%S%f')}"

        criar = self.client.post("/api/servicos/", json={
            "nome": nome_base,
            "categoria": "Mecanica",
            "descricao": "Servico criado no smoke test",
            "valor_padrao": 45.9
        })
        self.assertEqual(criar.status_code, 201)
        criado = criar.get_json()
        self.assertEqual(criado["nome"], nome_base)

        listar = self.client.get("/api/servicos/?nome=Servico Teste")
        self.assertEqual(listar.status_code, 200)
        dados_listagem = listar.get_json()
        self.assertIsInstance(dados_listagem, dict)
        self.assertIn("itens", dados_listagem)
        self.assertTrue(any(item["id"] == criado["id"] for item in dados_listagem["itens"]))

        obter = self.client.get(f"/api/servicos/{criado['id']}")
        self.assertEqual(obter.status_code, 200)
        self.assertEqual(obter.get_json()["id"], criado["id"])

        atualizar = self.client.put(f"/api/servicos/{criado['id']}", json={
            "categoria": "Eletrica",
            "valor_padrao": 55.5
        })
        self.assertEqual(atualizar.status_code, 200)
        self.assertEqual(atualizar.get_json()["categoria"], "Eletrica")

        excluir = self.client.delete(f"/api/servicos/{criado['id']}")
        self.assertEqual(excluir.status_code, 200)

    def test_api_pecas_crud_e_estoque(self):
        codigo_base = f"P{datetime.now().strftime('%H%M%S%f')}"
        nome_base = f"Peca Teste {datetime.now().strftime('%H%M%S%f')}"

        criar = self.client.post("/api/pecas/", json={
            "codigo": codigo_base,
            "nome": nome_base,
            "categoria": "Motor",
            "descricao": "Peca criada no smoke test",
            "estoque_atual": 10,
            "valor_custo": 15.5,
            "percentual_lucro": 20,
            "valor_unitario": 18.6
        })
        self.assertEqual(criar.status_code, 201)
        criada = criar.get_json()
        self.assertEqual(criada["codigo"], codigo_base)

        listar = self.client.get("/api/pecas/?nome=Peca Teste")
        self.assertEqual(listar.status_code, 200)
        dados_listagem = listar.get_json()
        self.assertIsInstance(dados_listagem, dict)
        self.assertIn("itens", dados_listagem)
        self.assertTrue(any(item["id"] == criada["id"] for item in dados_listagem["itens"]))

        obter = self.client.get(f"/api/pecas/{criada['id']}")
        self.assertEqual(obter.status_code, 200)
        self.assertEqual(obter.get_json()["id"], criada["id"])

        baixar = self.client.patch(f"/api/pecas/{criada['id']}/estoque", json={
            "operacao": "baixar",
            "quantidade": 3
        })
        self.assertEqual(baixar.status_code, 200)
        self.assertEqual(baixar.get_json()["estoque_atual"], 7.0)

        repor = self.client.patch(f"/api/pecas/{criada['id']}/estoque", json={
            "operacao": "repor",
            "quantidade": 5
        })
        self.assertEqual(repor.status_code, 200)
        self.assertEqual(repor.get_json()["estoque_atual"], 12.0)

        atualizar = self.client.put(f"/api/pecas/{criada['id']}", json={
            "categoria": "Eletrica",
            "valor_unitario": 21.0
        })
        self.assertEqual(atualizar.status_code, 200)
        self.assertEqual(atualizar.get_json()["categoria"], "Eletrica")

        excluir = self.client.delete(f"/api/pecas/{criada['id']}")
        self.assertEqual(excluir.status_code, 200)

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

        with self.app.app_context():
            movimento = MovimentoCaixa.query.filter_by(
                tipo='saida',
                categoria='despesa',
                descricao=descricao,
            ).order_by(MovimentoCaixa.id.desc()).first()
            self.assertIsNotNone(movimento)
            self.assertEqual(float(movimento.valor or 0), 12.34)

        excluir = self.client.delete(f"/api/fluxo/saidas/{dados_criacao['id']}")
        self.assertEqual(excluir.status_code, 200)

    def test_api_faturamento_ordem_com_desconto_e_pagamento_parcial(self):
        cliente_id = self._criar_cliente_teste()
        profissional_nome = self._obter_profissional_ativo()

        criar_ordem = self.client.post("/api/ordens/", json={
            "cliente_id": cliente_id,
            "profissional_responsavel": profissional_nome,
            "diagnostico": "Teste faturamento PDV",
            "servicos": [
                {"descricao_servico": "Servico A", "valor_servico": 100},
                {"descricao_servico": "Servico B", "valor_servico": 100}
            ],
            "pecas": [
                {"descricao_peca": "Peca A", "quantidade": 1, "valor_unitario": 100}
            ]
        })
        self.assertEqual(criar_ordem.status_code, 201)
        ordem = criar_ordem.get_json()

        faturar = self.client.post(f"/api/ordens/{ordem['id']}/faturamento", json={
            "desconto_percentual": 10,
            "pagamentos": [
                {"forma_pagamento": "Pix", "valor": 50, "observacao": "Entrada"},
                {"forma_pagamento": "Dinheiro", "valor": 100, "observacao": "Parcial"}
            ],
            "debito_vencimento": "2026-03-30",
            "debito_observacao": "Restante para depois"
        })
        self.assertEqual(faturar.status_code, 200)
        dados = faturar.get_json()

        self.assertEqual(dados["desconto_percentual"], 10.0)
        self.assertEqual(dados["desconto_valor"], 30.0)
        self.assertEqual(dados["total_cobrado"], 270.0)
        self.assertEqual(dados["total_pago"], 150.0)
        self.assertEqual(dados["saldo_pendente"], 120.0)
        self.assertEqual(dados["status_financeiro"], "Parcial")

        with self.app.app_context():
            movimentos = MovimentoCaixa.query.filter_by(
                tipo='entrada',
                categoria='pagamento_os',
                ordem_id=ordem['id'],
            ).all()
            self.assertEqual(len(movimentos), 2)
            self.assertAlmostEqual(sum(float(item.valor or 0) for item in movimentos), 150.0, places=2)


if __name__ == "__main__":
    unittest.main()
