# ===========================================
# services/validacao_service.py - Serviço de Validações
# ===========================================

import re
from datetime import datetime

class ValidacaoService:
    """Serviço para validações diversas"""
    
    @staticmethod
    def validar_cpf(cpf):
        """
        Valida se um CPF é válido
        
        Args:
            cpf: String do CPF (com ou sem formatação)
        
        Returns:
            bool: True se válido, False caso contrário
        """
        # Limpar CPF
        cpf = re.sub(r'[^\d]', '', cpf)
        
        # Verificar tamanho
        if len(cpf) != 11:
            return False
        
        # Verificar se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Calcular primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(cpf[i]) * (10 - i)
        resto = 11 - (soma % 11)
        digito1 = 0 if resto > 9 else resto
        
        if digito1 != int(cpf[9]):
            return False
        
        # Calcular segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(cpf[i]) * (11 - i)
        resto = 11 - (soma % 11)
        digito2 = 0 if resto > 9 else resto
        
        return digito2 == int(cpf[10])
    
    @staticmethod
    def validar_cnpj(cnpj):
        """
        Valida se um CNPJ é válido
        
        Args:
            cnpj: String do CNPJ (com ou sem formatação)
        
        Returns:
            bool: True se válido, False caso contrário
        """
        # Limpar CNPJ
        cnpj = re.sub(r'[^\d]', '', cnpj)
        
        # Verificar tamanho
        if len(cnpj) != 14:
            return False
        
        # Verificar se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Calcular primeiro dígito verificador
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = 0
        for i in range(12):
            soma += int(cnpj[i]) * pesos1[i]
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if digito1 != int(cnpj[12]):
            return False
        
        # Calcular segundo dígito verificador
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = 0
        for i in range(13):
            soma += int(cnpj[i]) * pesos2[i]
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return digito2 == int(cnpj[13])
    
    @staticmethod
    def validar_email(email):
        """
        Valida se um e-mail é válido
        
        Args:
            email: String do e-mail
        
        Returns:
            bool: True se válido, False caso contrário
        """
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(padrao, email) is not None
    
    @staticmethod
    def validar_telefone(telefone):
        """
        Valida se um telefone é válido (formato brasileiro)
        
        Args:
            telefone: String do telefone
        
        Returns:
            bool: True se válido, False caso contrário
        """
        # Limpar telefone
        telefone = re.sub(r'[^\d]', '', telefone)
        
        # Verificar tamanho (8 ou 9 dígitos + 2 do DDD)
        if len(telefone) not in [10, 11]:
            return False
        
        return True
    
    @staticmethod
    def validar_placa(placa):
        """
        Valida se uma placa de veículo é válida (formato antigo ou Mercosul)
        
        Args:
            placa: String da placa
        
        Returns:
            bool: True se válida, False caso contrário
        """
        # Formato antigo: AAA-9999
        padrao_antigo = r'^[A-Z]{3}-\d{4}$'
        
        # Formato Mercosul: AAA9A99
        padrao_mercosul = r'^[A-Z]{3}\d[A-Z]\d{2}$'
        
        # Limpar e converter para maiúsculas
        placa = placa.upper().strip()
        
        return (re.match(padrao_antigo, placa) is not None or 
                re.match(padrao_mercosul, placa) is not None)
    
    @staticmethod
    def validar_data(data, formato='%Y-%m-%d'):
        """
        Valida se uma data é válida
        
        Args:
            data: String da data
            formato: Formato esperado
        
        Returns:
            bool: True se válida, False caso contrário
        """
        try:
            datetime.strptime(data, formato)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validar_valor_monetario(valor):
        """
        Valida se um valor monetário é válido
        
        Args:
            valor: String ou número
        
        Returns:
            bool: True se válido, False caso contrário
        """
        try:
            if isinstance(valor, str):
                # Remover símbolos de moeda e espaços
                valor = re.sub(r'[R$\s]', '', valor)
                valor = valor.replace('.', '').replace(',', '.')
            
            valor_float = float(valor)
            return valor_float >= 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validar_quantidade(quantidade):
        """
        Valida se uma quantidade é válida
        
        Args:
            quantidade: Número da quantidade
        
        Returns:
            bool: True se válida, False caso contrário
        """
        try:
            qtd = float(quantidade)
            return qtd > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validar_ano(ano):
        """
        Valida se um ano é válido
        
        Args:
            ano: String ou número do ano
        
        Returns:
            bool: True se válido, False caso contrário
        """
        try:
            ano_int = int(ano)
            ano_atual = datetime.now().year
            return 1900 <= ano_int <= ano_atual + 1
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validar_km(km):
        """
        Valida se a quilometragem é válida
        
        Args:
            km: String ou número do KM
        
        Returns:
            bool: True se válido, False caso contrário
        """
        try:
            km_int = int(km)
            return km_int >= 0 and km_int <= 9999999
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validar_tanque(tanque):
        """
        Valida se a porcentagem do tanque é válida
        
        Args:
            tanque: String ou número da porcentagem
        
        Returns:
            bool: True se válido, False caso contrário
        """
        try:
            tanque_int = int(tanque)
            return 0 <= tanque_int <= 100
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validar_status_ordem(status):
        """
        Valida se o status da ordem é válido
        
        Args:
            status: String do status
        
        Returns:
            bool: True se válido, False caso contrário
        """
        status_validos = [
            'Aguardando', 'Aguardando peças', 
            'Em andamento', 'Concluído', 'Garantia'
        ]
        return status in status_validos
    
    @staticmethod
    def validar_categoria_saida(categoria):
        """
        Valida se a categoria de saída é válida
        
        Args:
            categoria: String da categoria
        
        Returns:
            bool: True se válida, False caso contrário
        """
        categorias_validas = [
            'Peças', 'Fornecedor', 'Aluguel', 'Salários',
            'Impostos', 'Ferramentas', 'Marketing', 'Outros'
        ]
        return categoria in categorias_validas