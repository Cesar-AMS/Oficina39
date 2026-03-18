from urllib.parse import quote

from integrations.base import IntegrationAdapter
from integrations.consulta_placa import normalizar_placa
from integrations.http_client import request_json


class PlacaFipeAdapter(IntegrationAdapter):
    provider_name = 'placafipe'
    requires_api_key = True

    def fetch(self, placa):
        return request_json(
            'https://api.placafipe.com.br/v1/consulta',
            headers=self.headers(),
            method='POST',
            data={'placa': normalizar_placa(placa)}
        )

    def normalize(self, payload):
        return {
            'fonte': self.provider_name,
            'placa': payload.get('placa') or payload.get('plate') or '',
            'fabricante': payload.get('marca') or payload.get('manufacturer') or '',
            'modelo': payload.get('modelo') or '',
            'ano': str(payload.get('ano_modelo') or payload.get('ano') or ''),
            'cor': payload.get('cor') or '',
            'combustivel': payload.get('combustivel') or '',
            'motor': payload.get('motor') or '',
            'observacao': payload.get('mensagem') or ''
        }


class FipeApiPlacaAdapter(IntegrationAdapter):
    provider_name = 'fipeapi'
    requires_api_key = True

    def fetch(self, placa):
        return request_json(
            f'https://fipeapi.com.br/api/placa/{quote(normalizar_placa(placa))}',
            headers=self.headers()
        )

    def normalize(self, payload):
        return {
            'fonte': self.provider_name,
            'placa': payload.get('placa') or '',
            'fabricante': payload.get('marca') or '',
            'modelo': payload.get('modelo') or '',
            'ano': str(payload.get('ano') or payload.get('ano_modelo') or ''),
            'cor': payload.get('cor') or '',
            'combustivel': payload.get('combustivel') or '',
            'motor': payload.get('motor') or '',
            'observacao': payload.get('mensagem') or ''
        }


PLACA_ADAPTERS = {
    PlacaFipeAdapter.provider_name: PlacaFipeAdapter,
    FipeApiPlacaAdapter.provider_name: FipeApiPlacaAdapter,
}
