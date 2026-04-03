import os
os.environ['TESTING'] = '1'

import unittest
from io import BytesIO
import json
import hmac
import hashlib
from datetime import datetime
from unittest.mock import patch

from app import create_app
from extensions import db
from models import ApiKey, Cliente, Comunicacao, MovimentoCaixa, Profissional, StatusLog, Webhook


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

    def _criar_cliente_teste_com_contato(self):
        with self.app.app_context():
            sufixo = datetime.now().strftime('%H%M%S%f')
            cliente = Cliente(
                nome_cliente=f"Cliente Contato {sufixo}",
                cpf=f"888{sufixo[:8]}",
                email=f"cliente{sufixo}@teste.local",
                telefone="11999998888",
            )
            db.session.add(cliente)
            db.session.commit()
            return cliente.id

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self._login_admin()}"}

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

    def _criar_profissional_teste(self):
        nome = f"Profissional Anexo {datetime.now().strftime('%H%M%S%f')}"
        resp = self.client.post("/api/profissionais/", json={
            "nome": nome,
            "cnpj": f"{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "ativo": True,
        }, headers=self._auth_headers())
        self.assertEqual(resp.status_code, 201)
        return resp.get_json()

    def _criar_peca_teste(self):
        codigo = f"PX{datetime.now().strftime('%H%M%S%f')}"
        resp = self.client.post("/api/pecas/", json={
            "codigo": codigo,
            "nome": f"Peca Anexo {datetime.now().strftime('%H%M%S%f')}",
            "categoria": "Teste",
            "estoque_atual": 5,
            "valor_unitario": 10,
        }, headers=self._auth_headers())
        self.assertEqual(resp.status_code, 201)
        return resp.get_json()

    def test_pagina_inicial(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def _login_admin(self):
        resp = self.client.post("/api/auth/login", json={
            "email": "admin@oficina39.local",
            "senha": "admin123",
        })
        self.assertEqual(resp.status_code, 200)
        return resp.get_json()["token"]

    def test_pagina_consultar_os(self):
        resp = self.client.get("/consultarOS.html")
        self.assertEqual(resp.status_code, 200)

    def test_api_auth_login_e_me(self):
        login = self.client.post("/api/auth/login", json={
            "email": "admin@oficina39.local",
            "senha": "admin123",
        })
        self.assertEqual(login.status_code, 200)
        dados_login = login.get_json()
        self.assertIn("token", dados_login)
        self.assertIn("usuario", dados_login)

        me = self.client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {dados_login['token']}",
        })
        self.assertEqual(me.status_code, 200)
        dados_me = me.get_json()
        self.assertEqual(dados_me["email"], "admin@oficina39.local")
        self.assertEqual(dados_me["perfil"], "admin")

    def test_api_comunicacoes_fila_basica(self):
        headers = self._auth_headers()
        criar = self.client.post("/api/comunicacoes/", json={
            "canal": "whatsapp",
            "destino": "5511999999999",
            "mensagem": "Teste de fila de comunicacao",
            "entidade_tipo": "ordem",
            "entidade_id": 1,
        }, headers=headers)
        self.assertEqual(criar.status_code, 201)
        comunicacao = criar.get_json()
        self.assertEqual(comunicacao["status"], "pendente")

        listar = self.client.get("/api/comunicacoes/?canal=whatsapp", headers=headers)
        self.assertEqual(listar.status_code, 200)
        payload = listar.get_json()
        self.assertTrue(any(item["id"] == comunicacao["id"] for item in payload["itens"]))

        processar = self.client.post(f"/api/comunicacoes/{comunicacao['id']}/processar", headers=headers)
        self.assertEqual(processar.status_code, 200)
        processada = processar.get_json()
        self.assertEqual(processada["status"], "falhou")
        self.assertTrue(processada["erro"])

    def test_api_templates_comunicacao_padrao(self):
        resp = self.client.get("/api/comunicacoes/templates", headers=self._auth_headers())
        self.assertEqual(resp.status_code, 200)
        itens = resp.get_json()
        nomes = {item["nome"] for item in itens}
        self.assertIn("os_criada", nomes)
        self.assertIn("os_concluida", nomes)
        self.assertIn("os_paga", nomes)

    def test_api_keys_criacao_e_rate_limit_integracoes(self):
        criar = self.client.post("/api/api-keys/", json={
            "nome": f"Integração Teste {datetime.now().strftime('%H%M%S%f')}",
            "permissoes": ["integracoes.leitura"],
            "rate_limit": 1,
            "ativa": True,
        }, headers=self._auth_headers())
        self.assertEqual(criar.status_code, 201)
        payload = criar.get_json()
        self.assertIn("api_key", payload)
        self.assertIn("secret", payload)

        api_key = payload["api_key"]
        secret = payload["secret"]
        headers = {
            "X-API-Key": api_key["key"],
            "X-API-Secret": secret,
        }

        primeira = self.client.get("/api/integracoes/status", headers=headers)
        self.assertEqual(primeira.status_code, 200)
        self.assertEqual(primeira.get_json()["status"], "ok")

        segunda = self.client.get("/api/integracoes/status", headers=headers)
        self.assertEqual(segunda.status_code, 429)

        with self.app.app_context():
            registro = ApiKey.query.filter_by(id=api_key["id"]).first()
            self.assertIsNotNone(registro)
            self.assertIsNotNone(registro.ultimo_uso)

    def test_api_webhooks_criacao_e_disparo_por_evento(self):
        api_key_resp = self.client.post("/api/api-keys/", json={
            "nome": f"Webhook Key {datetime.now().strftime('%H%M%S%f')}",
            "permissoes": ["integracoes.leitura"],
            "rate_limit": 10,
        }, headers=self._auth_headers())
        self.assertEqual(api_key_resp.status_code, 201)
        api_key_id = api_key_resp.get_json()["api_key"]["id"]

        criar_webhook = self.client.post("/api/webhooks/", json={
            "url": "https://webhook.teste.local/eventos",
            "eventos": ["cliente.criado", "os.criada"],
            "api_key_id": api_key_id,
            "ativo": True,
            "tentativas": 2,
            "timeout": 5,
        }, headers=self._auth_headers())
        self.assertEqual(criar_webhook.status_code, 201)
        webhook = criar_webhook.get_json()
        self.assertEqual(webhook["api_key_id"], api_key_id)

        secret = api_key_resp.get_json()["secret"]
        with patch("services.webhook_service.urllib_request.urlopen") as post_mock:
            post_mock.return_value.__enter__.return_value.status = 200
            sufixo = datetime.now().strftime('%H%M%S%f')
            criar_cliente = self.client.post("/api/clientes/", json={
                "nome_cliente": f"Cliente Webhook {sufixo}",
                "cpf": "52998224725",
                "telefone": "11999997777",
                "email": f"webhook{sufixo}@teste.local",
            }, headers=self._auth_headers())
            self.assertEqual(criar_cliente.status_code, 201)
            cliente_id = criar_cliente.get_json()["id"]
            self.assertTrue(cliente_id > 0)
            self.assertTrue(post_mock.called)
            request_obj = post_mock.call_args.args[0]
            headers = dict(request_obj.header_items())
            self.assertIn("X-webhook-signature", headers)
            corpo = json.loads(request_obj.data.decode("utf-8"))
            assinatura_esperada = hmac.new(
                secret.encode("utf-8"),
                json.dumps(corpo, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            self.assertEqual(headers["X-webhook-signature"], assinatura_esperada)

        with self.app.app_context():
            registro = Webhook.query.filter_by(id=webhook["id"]).first()
            self.assertIsNotNone(registro)
            self.assertEqual(registro.ultimo_status, 200)
            self.assertIsNotNone(registro.ultima_chamada)

    def test_api_publica_health_e_openapi(self):
        health = self.client.get("/api/public/health")
        self.assertEqual(health.status_code, 200)
        dados_health = health.get_json()
        self.assertEqual(dados_health["status"], "ok")

        openapi = self.client.get("/api/public/openapi.json")
        self.assertEqual(openapi.status_code, 200)
        spec = openapi.get_json()
        self.assertEqual(spec["openapi"], "3.0.3")
        self.assertIn("/api/integracoes/status", spec["paths"])

    def test_api_usuarios_crud_protegido(self):
        token = self._login_admin()
        sufixo = datetime.now().strftime('%H%M%S%f')

        criar = self.client.post("/api/usuarios/", json={
            "nome": f"Usuario Teste {sufixo}",
            "email": f"usuario{sufixo}@teste.local",
            "senha": "senha123",
            "perfil": "operador",
            "ativo": True,
        }, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(criar.status_code, 201)
        criado = criar.get_json()
        self.assertEqual(criado["perfil"], "operador")

        listar = self.client.get("/api/usuarios/", headers={
            "Authorization": f"Bearer {token}",
        })
        self.assertEqual(listar.status_code, 200)
        usuarios = listar.get_json()
        self.assertTrue(any(item["id"] == criado["id"] for item in usuarios))

        atualizar = self.client.put(f"/api/usuarios/{criado['id']}", json={
            "perfil": "visualizador",
            "ativo": False,
        }, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(atualizar.status_code, 200)
        dados_atualizados = atualizar.get_json()
        self.assertEqual(dados_atualizados["perfil"], "visualizador")
        self.assertFalse(dados_atualizados["ativo"])

    def test_pagina_relatorio_profissionais(self):
        resp = self.client.get("/relatorios/producao-profissionais")
        self.assertEqual(resp.status_code, 200)

    def test_api_ordens_lista(self):
        resp = self.client.get("/api/ordens/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), list)

    def test_api_preview_ordem_retorna_pdf_sem_salvar(self):
        cliente_id = self._criar_cliente_teste_com_contato()
        profissional_nome = self._obter_profissional_ativo()
        resp = self.client.post("/api/ordens/preview", json={
            "cliente_id": cliente_id,
            "profissional_responsavel": profissional_nome,
            "diagnostico": "Preview de OS",
            "servicos": [
                {"descricao_servico": "Servico preview", "valor_servico": 80}
            ],
            "pecas": [
                {"descricao_peca": "Peca preview", "quantidade": 2, "valor_unitario": 10}
            ]
        }, headers=self._auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/pdf")
        self.assertTrue(resp.data.startswith(b"%PDF"))

    def test_api_servicos_crud(self):
        nome_base = f"Servico Teste {datetime.now().strftime('%H%M%S%f')}"

        criar = self.client.post("/api/servicos/", json={
            "nome": nome_base,
            "categoria": "Mecanica",
            "descricao": "Servico criado no smoke test",
            "valor_padrao": 45.9
        }, headers=self._auth_headers())
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
        }, headers=self._auth_headers())
        self.assertEqual(atualizar.status_code, 200)
        self.assertEqual(atualizar.get_json()["categoria"], "Eletrica")

        excluir = self.client.delete(f"/api/servicos/{criado['id']}", headers=self._auth_headers())
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
        }, headers=self._auth_headers())
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
        }, headers=self._auth_headers())
        self.assertEqual(baixar.status_code, 200)
        self.assertEqual(baixar.get_json()["estoque_atual"], 7.0)

        repor = self.client.patch(f"/api/pecas/{criada['id']}/estoque", json={
            "operacao": "repor",
            "quantidade": 5
        }, headers=self._auth_headers())
        self.assertEqual(repor.status_code, 200)
        self.assertEqual(repor.get_json()["estoque_atual"], 12.0)

        atualizar = self.client.put(f"/api/pecas/{criada['id']}", json={
            "categoria": "Eletrica",
            "valor_unitario": 21.0
        }, headers=self._auth_headers())
        self.assertEqual(atualizar.status_code, 200)
        self.assertEqual(atualizar.get_json()["categoria"], "Eletrica")

        excluir = self.client.delete(f"/api/pecas/{criada['id']}", headers=self._auth_headers())
        self.assertEqual(excluir.status_code, 200)

    def test_api_ordens_busca_cliente_ou_cpf(self):
        resp = self.client.get("/api/ordens/busca?cliente=teste")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), list)

    def test_api_config_contador(self):
        resp = self.client.get("/api/config/contador", headers=self._auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), dict)

    def test_api_producao_profissionais(self):
        resp = self.client.get("/api/relatorios/producao-profissionais")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.get_json(), list)

    def test_api_relatorios_financeiros_estrutura(self):
        painel = self.client.get("/api/relatorios/painel-dia")
        self.assertEqual(painel.status_code, 200)
        dados_painel = painel.get_json()
        self.assertIn("faturamento_hoje", dados_painel)
        self.assertIn("saidas_hoje", dados_painel)
        self.assertIn("saldo_hoje", dados_painel)

        contabilidade = self.client.get("/api/relatorios/contabilidade-geral", headers=self._auth_headers())
        self.assertEqual(contabilidade.status_code, 200)
        dados_contabilidade = contabilidade.get_json()
        self.assertIn("faturamento_bruto", dados_contabilidade)
        self.assertIn("total_saidas", dados_contabilidade)
        self.assertIn("saldo_operacional", dados_contabilidade)
        self.assertIn("pagamentos", dados_contabilidade)

    def test_api_operacional_servicos_pecas_saidas(self):
        resp = self.client.get("/api/relatorios/operacional-servicos-pecas-saidas")
        self.assertEqual(resp.status_code, 200)
        dados = resp.get_json()
        self.assertIsInstance(dados, dict)
        self.assertIn("servicos", dados)
        self.assertIn("pecas", dados)
        self.assertIn("saidas", dados)
        self.assertIn("resumo", dados)

    def test_api_exportacao_excel_operacional(self):
        resp = self.client.get("/api/relatorios/operacional-servicos-pecas-saidas/exportar-excel")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.mimetype,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(resp.data.startswith(b"PK"))

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
        criar = self.client.post("/api/fluxo/saidas", json=payload, headers=self._auth_headers())
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

        excluir = self.client.delete(f"/api/fluxo/saidas/{dados_criacao['id']}", headers=self._auth_headers())
        self.assertEqual(excluir.status_code, 200)

    def test_api_faturamento_ordem_com_desconto_e_pagamento_parcial(self):
        cliente_id = self._criar_cliente_teste_com_contato()
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
        }, headers=self._auth_headers())
        self.assertEqual(criar_ordem.status_code, 201)
        ordem = criar_ordem.get_json()
        self.assertIn("preview_pdf_url", ordem)
        self.assertIn("download_pdf_url", ordem)
        self.assertIn("whatsapp_web_url", ordem)

        faturar = self.client.post(f"/api/ordens/{ordem['id']}/faturamento", json={
            "desconto_percentual": 10,
            "pagamentos": [
                {"forma_pagamento": "Pix", "valor": 50, "observacao": "Entrada"},
                {"forma_pagamento": "Dinheiro", "valor": 100, "observacao": "Parcial"}
            ],
            "debito_vencimento": "2026-03-30",
            "debito_observacao": "Restante para depois"
        }, headers=self._auth_headers())
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

            comunicacoes = Comunicacao.query.filter_by(entidade_tipo='ordem', entidade_id=ordem['id']).all()
            templates = {((item.metadata_json or {}).get('template_nome')) for item in comunicacoes}
            self.assertIn('os_criada', templates)
            self.assertIn('os_concluida', templates)

    def test_api_status_log_unificado_ordem(self):
        cliente_id = self._criar_cliente_teste()
        profissional_nome = self._obter_profissional_ativo()

        criar_ordem = self.client.post("/api/ordens/", json={
            "cliente_id": cliente_id,
            "profissional_responsavel": profissional_nome,
            "diagnostico": "Teste historico de status",
            "servicos": [
                {"descricao_servico": "Servico X", "valor_servico": 50}
            ]
        }, headers=self._auth_headers())
        self.assertEqual(criar_ordem.status_code, 201)
        ordem = criar_ordem.get_json()

        atualizar = self.client.patch(f"/api/ordens/{ordem['id']}/status", json={
            "status": "Em andamento",
            "observacao": "Iniciado no teste"
        }, headers=self._auth_headers())
        self.assertEqual(atualizar.status_code, 200)

        with self.app.app_context():
            log = StatusLog.query.filter_by(
                entidade_tipo='ordem',
                entidade_id=ordem['id'],
                status_novo='Em andamento',
            ).order_by(StatusLog.id.desc()).first()
            self.assertIsNotNone(log)
            self.assertEqual(log.status_anterior, 'Aguardando')

        listar = self.client.get(f"/api/ordens/{ordem['id']}/status-log")
        self.assertEqual(listar.status_code, 200)
        logs = listar.get_json()
        self.assertIsInstance(logs, list)
        self.assertTrue(any(item["status_novo"] == "Em andamento" for item in logs))

    def test_api_os_quitada_dispara_template_pagamento(self):
        cliente_id = self._criar_cliente_teste_com_contato()
        profissional_nome = self._obter_profissional_ativo()

        criar_ordem = self.client.post("/api/ordens/", json={
            "cliente_id": cliente_id,
            "profissional_responsavel": profissional_nome,
            "diagnostico": "Teste comunicacao quitacao",
            "servicos": [
                {"descricao_servico": "Servico quitacao", "valor_servico": 100}
            ]
        }, headers=self._auth_headers())
        self.assertEqual(criar_ordem.status_code, 201)
        ordem = criar_ordem.get_json()

        faturar = self.client.post(f"/api/ordens/{ordem['id']}/faturamento", json={
            "pagamentos": [
                {"forma_pagamento": "Pix", "valor": 100, "observacao": "Quitacao total"}
            ]
        }, headers=self._auth_headers())
        self.assertEqual(faturar.status_code, 200)

        with self.app.app_context():
            comunicacoes = Comunicacao.query.filter_by(entidade_tipo='ordem', entidade_id=ordem['id']).all()
            templates = {((item.metadata_json or {}).get('template_nome')) for item in comunicacoes}
            self.assertIn('os_paga', templates)

    def test_historico_unificado_inclui_status_e_auditoria(self):
        cliente_id = self._criar_cliente_teste()
        profissional_nome = self._obter_profissional_ativo()

        criar_ordem = self.client.post("/api/ordens/", json={
            "cliente_id": cliente_id,
            "profissional_responsavel": profissional_nome,
            "diagnostico": "Teste historico unificado",
            "servicos": [
                {"descricao_servico": "Servico Hist", "valor_servico": 80}
            ]
        }, headers=self._auth_headers())
        self.assertEqual(criar_ordem.status_code, 201)
        ordem = criar_ordem.get_json()

        atualizar = self.client.put(f"/api/ordens/{ordem['id']}", json={
            "diagnostico": "Teste historico unificado atualizado",
            "servicos": [
                {"descricao_servico": "Servico Hist", "valor_servico": 95}
            ]
        }, headers=self._auth_headers())
        self.assertEqual(atualizar.status_code, 200)

        mudar_status = self.client.patch(f"/api/ordens/{ordem['id']}/status", json={
            "status": "Em andamento",
            "observacao": "Mudanca para validar historico"
        }, headers=self._auth_headers())
        self.assertEqual(mudar_status.status_code, 200)

        historico_resp = self.client.get(
            f"/api/historico/unificado?entidade_tipo=ordem&entidade_id={ordem['id']}&limite=20"
        )
        self.assertEqual(historico_resp.status_code, 200)
        historico = historico_resp.get_json()
        self.assertIsInstance(historico, list)
        tipos = {item['tipo'] for item in historico}
        self.assertIn('status_log', tipos)
        self.assertIn('auditoria', tipos)

    def test_api_anexos_ordem_legado_usa_dominio_generico(self):
        cliente_id = self._criar_cliente_teste()
        profissional_nome = self._obter_profissional_ativo()

        criar_ordem = self.client.post("/api/ordens/", json={
            "cliente_id": cliente_id,
            "profissional_responsavel": profissional_nome,
            "diagnostico": "Teste anexo generico",
            "servicos": [
                {"descricao_servico": "Servico com anexo", "valor_servico": 70}
            ]
        }, headers=self._auth_headers())
        self.assertEqual(criar_ordem.status_code, 201)
        ordem = criar_ordem.get_json()

        upload = self.client.post(
            f"/api/ordens/{ordem['id']}/anexos",
            data={
                "categoria": "diagnostico",
                "descricao": "Arquivo de teste",
                "arquivo": (BytesIO(b"conteudo de anexo"), "teste_anexo.txt"),
            },
            content_type="multipart/form-data",
            headers=self._auth_headers(),
        )
        self.assertEqual(upload.status_code, 201)
        anexo = upload.get_json()
        self.assertEqual(anexo["entidade_tipo"], "ordem")
        self.assertEqual(anexo["entidade_id"], ordem["id"])

        listar = self.client.get(f"/api/ordens/{ordem['id']}/anexos")
        self.assertEqual(listar.status_code, 200)
        anexos = listar.get_json()
        self.assertTrue(any(item["id"] == anexo["id"] for item in anexos))

        download = self.client.get(f"/api/ordens/{ordem['id']}/anexos/{anexo['id']}/download")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.data, b"conteudo de anexo")

        excluir = self.client.delete(f"/api/ordens/{ordem['id']}/anexos/{anexo['id']}", headers=self._auth_headers())
        self.assertEqual(excluir.status_code, 200)

    def test_api_anexos_cliente_profissional_e_peca(self):
        cliente_id = self._criar_cliente_teste()
        profissional = self._criar_profissional_teste()
        peca = self._criar_peca_teste()

        upload_cliente = self.client.post(
            f"/api/clientes/{cliente_id}/anexos",
            data={"arquivo": (BytesIO(b"cliente"), "cliente.txt")},
            content_type="multipart/form-data",
            headers=self._auth_headers(),
        )
        self.assertEqual(upload_cliente.status_code, 201)
        anexo_cliente = upload_cliente.get_json()
        self.assertEqual(anexo_cliente["entidade_tipo"], "cliente")

        listar_cliente = self.client.get(f"/api/clientes/{cliente_id}/anexos")
        self.assertEqual(listar_cliente.status_code, 200)
        self.assertTrue(any(item["id"] == anexo_cliente["id"] for item in listar_cliente.get_json()))

        upload_prof = self.client.post(
            f"/api/profissionais/{profissional['id']}/anexos",
            data={"arquivo": (BytesIO(b"profissional"), "profissional.txt")},
            content_type="multipart/form-data",
            headers=self._auth_headers(),
        )
        self.assertEqual(upload_prof.status_code, 201)
        anexo_prof = upload_prof.get_json()
        self.assertEqual(anexo_prof["entidade_tipo"], "profissional")

        download_prof = self.client.get(f"/api/profissionais/{profissional['id']}/anexos/{anexo_prof['id']}/download")
        self.assertEqual(download_prof.status_code, 200)
        self.assertEqual(download_prof.data, b"profissional")

        upload_peca = self.client.post(
            f"/api/pecas/{peca['id']}/anexos",
            data={"arquivo": (BytesIO(b"peca"), "peca.txt")},
            content_type="multipart/form-data",
            headers=self._auth_headers(),
        )
        self.assertEqual(upload_peca.status_code, 201)
        anexo_peca = upload_peca.get_json()
        self.assertEqual(anexo_peca["entidade_tipo"], "peca")

        excluir_peca = self.client.delete(f"/api/pecas/{peca['id']}/anexos/{anexo_peca['id']}", headers=self._auth_headers())
        self.assertEqual(excluir_peca.status_code, 200)

        excluir_cliente = self.client.delete(f"/api/clientes/{cliente_id}/anexos/{anexo_cliente['id']}", headers=self._auth_headers())
        self.assertEqual(excluir_cliente.status_code, 200)

        excluir_prof = self.client.delete(f"/api/profissionais/{profissional['id']}/anexos/{anexo_prof['id']}", headers=self._auth_headers())
        self.assertEqual(excluir_prof.status_code, 200)


if __name__ == "__main__":
    unittest.main()
