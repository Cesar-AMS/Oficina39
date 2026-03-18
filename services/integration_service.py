import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from integrations.consulta_placa import normalizar_placa
from integrations.viacep import endpoint_por_cep
from repositories import cliente_repository, config_repository


def _http_json(url, headers=None, method='GET', data=None, timeout=8):
    request = Request(url, headers=headers or {}, method=method)
    if data is not None:
        payload = json.dumps(data).encode('utf-8')
        request.add_header('Content-Type', 'application/json')
    else:
        payload = None
    with urlopen(request, data=payload, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or 'utf-8'
        return json.loads(response.read().decode(charset))


def _config():
    return config_repository.obter_config_contador()


def _ordem_provedores(tipo):
    config = _config()
    if not config:
        return ['viacep', 'brasilapi'] if tipo == 'cep' else []

    if tipo == 'cep':
        lista = [config.cep_provider_ativo, config.cep_provider_primario, config.cep_provider_secundario]
    else:
        lista = [config.placa_provider_ativo, config.placa_provider_primario, config.placa_provider_secundario]

    retorno = []
    for item in lista:
        nome = (item or '').strip().lower()
        if nome and nome not in retorno:
            retorno.append(nome)
    if tipo == 'cep':
        for padrao in ['viacep', 'brasilapi']:
            if padrao not in retorno:
                retorno.append(padrao)
    return retorno


def _api_key(tipo, posicao):
    config = _config()
    if not config:
        return None
    if tipo == 'cep' and posicao == 'primaria':
        return config.cep_api_key_primaria
    if tipo == 'cep' and posicao == 'secundaria':
        return config.cep_api_key_secundaria
    if tipo == 'placa' and posicao == 'primaria':
        return config.placa_api_key_primaria
    if tipo == 'placa' and posicao == 'secundaria':
        return config.placa_api_key_secundaria
    return None


def _api_key_por_provedor(tipo, provedor):
    config = _config()
    if not config:
        return None
    primario = (config.cep_provider_primario if tipo == 'cep' else config.placa_provider_primario or '').strip().lower()
    secundario = (config.cep_provider_secundario if tipo == 'cep' else config.placa_provider_secundario or '').strip().lower()
    provedor = (provedor or '').strip().lower()
    if provedor and provedor == primario:
        return _api_key(tipo, 'primaria')
    if provedor and provedor == secundario:
        return _api_key(tipo, 'secundaria')
    return None


def consultar_cep(cep):
    cep_limpo = ''.join(ch for ch in (cep or '') if ch.isdigit())
    if len(cep_limpo) != 8:
        raise ValueError('CEP inválido. Informe 8 dígitos.')

    erros = []
    for provedor in _ordem_provedores('cep'):
        try:
            if provedor == 'viacep':
                dados = _http_json(endpoint_por_cep(cep_limpo))
                if dados.get('erro'):
                    raise ValueError('CEP não encontrado.')
                return {
                    'fonte': 'viacep',
                    'cep': dados.get('cep') or cep_limpo,
                    'logradouro': dados.get('logradouro') or '',
                    'bairro': dados.get('bairro') or '',
                    'cidade': dados.get('localidade') or '',
                    'estado': dados.get('uf') or '',
                    'complemento': dados.get('complemento') or ''
                }
            if provedor == 'brasilapi':
                dados = _http_json(f'https://brasilapi.com.br/api/cep/v1/{quote(cep_limpo)}')
                return {
                    'fonte': 'brasilapi',
                    'cep': dados.get('cep') or cep_limpo,
                    'logradouro': dados.get('street') or '',
                    'bairro': dados.get('neighborhood') or '',
                    'cidade': dados.get('city') or '',
                    'estado': dados.get('state') or '',
                    'complemento': ''
                }
            raise ValueError(f'Provedor de CEP "{provedor}" não implementado.')
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            erros.append(f'{provedor}: {exc}')

    raise RuntimeError('Falha ao consultar CEP. ' + ' | '.join(erros))


def _normalizar_placa_payload(provedor, dados):
    if provedor == 'placafipe':
        return {
            'fonte': 'placafipe',
            'placa': dados.get('placa') or dados.get('plate') or '',
            'fabricante': dados.get('marca') or dados.get('manufacturer') or '',
            'modelo': dados.get('modelo') or '',
            'ano': str(dados.get('ano_modelo') or dados.get('ano') or ''),
            'cor': dados.get('cor') or '',
            'combustivel': dados.get('combustivel') or '',
            'motor': dados.get('motor') or '',
            'observacao': dados.get('mensagem') or ''
        }
    if provedor == 'fipeapi':
        return {
            'fonte': 'fipeapi',
            'placa': dados.get('placa') or '',
            'fabricante': dados.get('marca') or '',
            'modelo': dados.get('modelo') or '',
            'ano': str(dados.get('ano') or dados.get('ano_modelo') or ''),
            'cor': dados.get('cor') or '',
            'combustivel': dados.get('combustivel') or '',
            'motor': dados.get('motor') or '',
            'observacao': dados.get('mensagem') or ''
        }
    return dados


def _consultar_placa_externa(placa, provedor):
    api_key = _api_key_por_provedor('placa', provedor)
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
        headers['X-API-Key'] = api_key

    placa_normalizada = normalizar_placa(placa)
    if provedor == 'placafipe':
        dados = _http_json(
            'https://api.placafipe.com.br/v1/consulta',
            headers=headers,
            method='POST',
            data={'placa': placa_normalizada}
        )
        return _normalizar_placa_payload(provedor, dados)
    if provedor == 'fipeapi':
        dados = _http_json(
            f'https://fipeapi.com.br/api/placa/{quote(placa_normalizada)}',
            headers=headers
        )
        return _normalizar_placa_payload(provedor, dados)
    raise ValueError(f'Provedor de placa "{provedor}" não implementado.')


def consultar_placa(placa):
    placa_normalizada = normalizar_placa(placa)
    if len(placa_normalizada) < 7:
        raise ValueError('Placa inválida. Informe ao menos 7 caracteres.')

    cliente_local = cliente_repository.buscar_por_placa(placa_normalizada if '-' in placa_normalizada else f'{placa_normalizada[:3]}-{placa_normalizada[3:]}')
    if cliente_local:
        return {
            'fonte': 'cadastro_local',
            'tipo_preenchimento': 'completo',
            'nome_cliente': cliente_local.nome_cliente or '',
            'cpf': cliente_local.cpf or '',
            'telefone': cliente_local.telefone or '',
            'email': cliente_local.email or '',
            'endereco': cliente_local.endereco or '',
            'cidade': cliente_local.cidade or '',
            'estado': cliente_local.estado or '',
            'cep': cliente_local.cep or '',
            'placa': cliente_local.placa or placa_normalizada,
            'fabricante': cliente_local.fabricante or '',
            'modelo': cliente_local.modelo or '',
            'ano': cliente_local.ano or '',
            'cor': cliente_local.cor or '',
            'combustivel': cliente_local.combustivel or '',
            'motor': cliente_local.motor or '',
            'observacao': 'Dados carregados do banco local para evitar nova consulta externa.'
        }

    erros = []
    for provedor in _ordem_provedores('placa'):
        try:
            return _consultar_placa_externa(placa_normalizada, provedor)
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
            erros.append(f'{provedor}: {exc}')

    raise RuntimeError('Falha ao consultar placa. Configure a API em Configurações. ' + ' | '.join(erros))
