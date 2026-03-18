from urllib.parse import quote


def endpoint_por_cep(cep):
    cep_limpo = ''.join(ch for ch in (cep or '') if ch.isdigit())
    return f"https://viacep.com.br/ws/{quote(cep_limpo)}/json/"
