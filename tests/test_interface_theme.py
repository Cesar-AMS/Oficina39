import os
os.environ['TESTING'] = '1'

import re
import unittest

from app import create_app


def _hex_to_rgb(value: str):
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _linearize(channel: float) -> float:
    if channel <= 0.03928:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _luminance(color: str) -> float:
    r, g, b = _hex_to_rgb(color)
    r, g, b = _linearize(r), _linearize(g), _linearize(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(color_a: str, color_b: str) -> float:
    lum_a = _luminance(color_a)
    lum_b = _luminance(color_b)
    lighter = max(lum_a, lum_b)
    darker = min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


class InterfaceThemeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(testing=True)
        cls.client = cls.app.test_client()
        css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'css', 'style.css')
        with open(css_path, 'r', encoding='utf-8') as css_file:
            cls.css = css_file.read()

    def test_interface_carrega_com_css_novo(self):
        for rota in ('/', '/nova-os', '/consultarOS.html', '/cadastroCliente.html'):
            resposta = self.client.get(rota)
            self.assertEqual(resposta.status_code, 200)
            self.assertIn('/static/css/style.css', resposta.get_data(as_text=True))

    def test_botoes_tem_hover_effect(self):
        self.assertIn('.btn:hover', self.css)
        self.assertIn('transform: translateY(-1px);', self.css)
        self.assertIn('box-shadow: var(--shadow-md);', self.css)

    def test_layout_responsivo_mobile(self):
        self.assertIn('@media (max-width: 768px)', self.css)
        self.assertIn('@media (max-width: 640px)', self.css)
        self.assertRegex(self.css, r'overflow-x:\s*auto;')
        self.assertIn('.menu-lateral.is-open', self.css)

    def test_cores_atendem_contraste(self):
        pares = [
            ('#1f2937', '#ffffff'),
            ('#ffffff', '#1a56db'),
            ('#4b5563', '#f3f4f6'),
        ]
        for foreground, background in pares:
            self.assertGreaterEqual(_contrast_ratio(foreground, background), 4.5)

    def test_paginas_densas_recebem_layout_refinado(self):
        config = self.client.get('/config_contador.html')
        self.assertEqual(config.status_code, 200)
        html_config = config.get_data(as_text=True)
        self.assertIn('config-page-grid', html_config)
        self.assertIn('config-card-eyebrow', html_config)

        fluxo = self.client.get('/fluxo_caixa.html')
        self.assertEqual(fluxo.status_code, 200)
        html_fluxo = fluxo.get_data(as_text=True)
        self.assertIn('caixa-resumo-grid', html_fluxo)
        self.assertIn('caixa-toolbar', html_fluxo)

        visualizar = self.client.get('/visualizarOS.html?id=1')
        self.assertEqual(visualizar.status_code, 200)
        html_visualizar = visualizar.get_data(as_text=True)
        self.assertIn('visualizar-layout-grid', html_visualizar)
        self.assertIn('status-chip-topo', html_visualizar)


if __name__ == '__main__':
    unittest.main()
