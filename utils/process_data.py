def process_data(conteudo):
    conteudo = conteudo.replace('\r\n', '\n').replace('\r', '\n')
    linhas = conteudo.strip().split('\n')
    linhas_limpas = [linha.strip() for linha in linhas if linha.strip()]
    return '\n'.join(linhas_limpas)
