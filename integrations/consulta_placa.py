def normalizar_placa(placa):
    return (placa or '').replace('-', '').strip().upper()
