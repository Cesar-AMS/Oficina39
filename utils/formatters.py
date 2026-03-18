import re


def somente_digitos(valor):
    return re.sub(r'\D', '', valor or '')


def texto_limpo(valor):
    return (valor or '').strip()


def cpf_sem_mascara(valor):
    return somente_digitos(valor)


def cnpj_sem_mascara(valor):
    return somente_digitos(valor)
