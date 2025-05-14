MAPA_UF = {
    "12": "AC", "27": "AL", "13": "AM", "16": "AP", "29": "BA", "23": "CE",
    "53": "DF", "32": "ES", "52": "GO", "21": "MA", "31": "MG", "50": "MS",
    "51": "MT", "15": "PA", "25": "PB", "26": "PE", "22": "PI", "41": "PR",
    "33": "RJ", "24": "RN", "43": "RS", "11": "RO", "14": "RR", "42": "SC",
    "28": "SE", "35": "SP", "17": "TO"
}

def obter_sigla_estado(codigo_municipio):
    if not codigo_municipio or len(codigo_municipio) < 2:
        return None
    return MAPA_UF.get(codigo_municipio[:2])