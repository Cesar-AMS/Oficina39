from urllib.error import HTTPError, URLError

from integrations.cep_adapters import CEP_ADAPTERS
from integrations.consulta_placa import normalizar_placa
from integrations.placa_adapters import PLACA_ADAPTERS
from repositories import cliente_repository, config_repository


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
            adapter_cls = CEP_ADAPTERS.get(provedor)
            if not adapter_cls:
                raise ValueError(f'Provedor de CEP "{provedor}" não implementado.')
            adapter = adapter_cls(api_key=_api_key_por_provedor('cep', provedor))
            return adapter.normalize(adapter.fetch(cep_limpo))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            erros.append(f'{provedor}: {exc}')

    raise RuntimeError('Falha ao consultar CEP. ' + ' | '.join(erros))


def _consultar_placa_externa(placa, provedor):
    adapter_cls = PLACA_ADAPTERS.get(provedor)
    if not adapter_cls:
        raise ValueError(f'Provedor de placa "{provedor}" não implementado.')
    adapter = adapter_cls(api_key=_api_key_por_provedor('placa', provedor))
    return adapter.normalize(adapter.fetch(placa))


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
