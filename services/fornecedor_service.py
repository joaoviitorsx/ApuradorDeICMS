from db.conexao import conectar_banco, fechar_banco
from utils.cnpj import processar_cnpjs
import asyncio

async def cadastro_fornecedores(nome_banco):
    conexao = conectar_banco(nome_banco)
    cursor = conexao.cursor()

    try:
        cursor.execute("""
            SHOW COLUMNS FROM cadastro_fornecedores
            WHERE Field IN ('cnae', 'decreto', 'uf', 'simples')
        """)
        colunas = [row[0] for row in cursor.fetchall()]

        if not all(col in colunas for col in ['cnae', 'decreto', 'uf', 'simples']):
            print("Colunas obrigatórias ausentes em cadastro_fornecedores.")
            return

        cursor.execute("""
            SELECT cnpj FROM cadastro_fornecedores
            WHERE (cnae IS NULL OR cnae = '')
              AND (decreto IS NULL OR decreto = '')
              AND (uf IS NULL OR uf = '')
        """)
        cnpjs_para_consultar = [row[0] for row in cursor.fetchall()]

        if not cnpjs_para_consultar:
            print("Nenhum CNPJ pendente de enriquecimento.")
            return

        resultados = await processar_cnpjs(cnpjs_para_consultar)

        for cnpj, (cnae, status, uf, simples) in resultados.items():
            decreto = 'Não' if 'ATIVA' in status.upper() else 'Sim'

            cursor.execute("""
                UPDATE cadastro_fornecedores
                SET cnae = %s, decreto = %s, uf = %s, simples = %s
                WHERE cnpj = %s
            """, (cnae, decreto, uf, simples, cnpj))

        conexao.commit()
        print(f"Enriquecimento finalizado para {len(resultados)} CNPJs.")

    except Exception as e:
        print(f"Erro ao enriquecer fornecedores: {e}")
        conexao.rollback()

    finally:
        cursor.close()
        fechar_banco(conexao)

