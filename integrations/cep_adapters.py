from urllib.parse import quote

from integrations.base import IntegrationAdapter
from integrations.http_client import request_json
from integrations.viacep import endpoint_por_cep


class ViaCepAdapter(IntegrationAdapter):
    provider_name = 'viacep'

    def fetch(self, cep):
        return request_json(endpoint_por_cep(cep), headers=self.headers())

    def normalize(self, payload):
        if payload.get('erro'):
            raise ValueError('CEP não encontrado.')
        return {
            'fonte': self.provider_name,
            'cep': payload.get('cep') or '',
            'logradouro': payload.get('logradouro') or '',
            'bairro': payload.get('bairro') or '',
            'cidade': payload.get('localidade') or '',
            'estado': payload.get('uf') or '',
            'complemento': payload.get('complemento') or ''
        }


class BrasilApiCepAdapter(IntegrationAdapter):
    provider_name = 'brasilapi'

    def fetch(self, cep):
        return request_json(f'https://brasilapi.com.br/api/cep/v1/{quote(cep)}', headers=self.headers())

    def normalize(self, payload):
        return {
            'fonte': self.provider_name,
            'cep': payload.get('cep') or '',
            'logradouro': payload.get('street') or '',
            'bairro': payload.get('neighborhood') or '',
            'cidade': payload.get('city') or '',
            'estado': payload.get('state') or '',
            'complemento': ''
        }


CEP_ADAPTERS = {
    ViaCepAdapter.provider_name: ViaCepAdapter,
    BrasilApiCepAdapter.provider_name: BrasilApiCepAdapter,
}
