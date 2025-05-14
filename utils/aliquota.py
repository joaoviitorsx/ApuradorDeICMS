def formatar_aliquota(valor):
    valor = str(valor).strip().upper()

    if valor in ["", None]:
        return ""
    
    if valor in ["ST", "ISENTO", "PAUTA"]:
        return valor

    valor = valor.replace(',', '.').replace('%', '')

    try:
        numero = float(valor)
        return f"{numero:.2f}%"
    except ValueError:
        return valor
