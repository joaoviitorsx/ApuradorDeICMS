import pandas as pd
from db.conexao import conectar_banco, fechar_banco
from utils.mensagem import mensagem_erro, mensagem_sucesso
from utils.aliquota import formatar_aliquota

CAMPOS_ESPERADOS = ['CODIGO', 'PRODUTO', 'NCM', 'ALIQUOTA']

def formatar_aliquota(valor):
    valor = str(valor).strip().upper()
    if valor in ["ST", "ISENTO", "PAUTA"]:
        return valor
    try:
        num = float(valor.replace(',', '.'))
        return f"{num:.2f}%"
    except:
        return valor if '%' in valor else f"{valor}%"

def normalizar_colunas(df):
    df.columns = [col.strip().upper().replace(" ", "").replace("_", "") for col in df.columns]
    return df

def mapear_colunas(df):
    colunas_normalizadas = {
        col: col.upper().strip().replace(" ", "").replace("_", "")
        for col in df.columns
    }
    mapeamento = {}

    for campo in CAMPOS_ESPERADOS:
        for original, normalizado in colunas_normalizadas.items():
            if campo == normalizado:
                mapeamento[campo] = original
                break
    return mapeamento

def importar_planilha_tributacao(path_arquivo, nome_banco):
    try:
        df = pd.read_excel(path_arquivo, dtype=str)
        df = normalizar_colunas(df)
        mapeamento = mapear_colunas(df)

        if len(mapeamento) < 4:
            mensagem_erro("Planilha não contém todas as colunas obrigatórias: CODIGO, PRODUTO, NCM, ALIQUOTA.")
            return

        df_filtrado = df[[mapeamento[c] for c in CAMPOS_ESPERADOS]].copy()
        df_filtrado.columns = CAMPOS_ESPERADOS

        df_filtrado['ALIQUOTA'] = df_filtrado['ALIQUOTA'].apply(formatar_aliquota)
        dados_para_inserir = df_filtrado.values.tolist()

        conexao = conectar_banco(nome_banco)
        cursor = conexao.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cadastro_tributacao (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo VARCHAR(20) UNIQUE,
                produto VARCHAR(100),
                ncm VARCHAR(20),
                aliquota VARCHAR(20),
                aliquota_antiga VARCHAR(20),
                data_inicial DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.executemany("""
            INSERT INTO cadastro_tributacao (codigo, produto, ncm, aliquota)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            produto = VALUES(produto),
            ncm = VALUES(ncm),
            aliquota = VALUES(aliquota)
        """, dados_para_inserir)

        conexao.commit()
        mensagem_sucesso(f"Tributação importada com sucesso! ({len(dados_para_inserir)} registros)")
    
    except Exception as e:
        mensagem_erro(f"Erro ao importar tributação: {e}")
    
    finally:
        fechar_banco(conexao)
