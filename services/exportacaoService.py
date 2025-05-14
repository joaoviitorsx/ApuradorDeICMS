import pandas as pd
from db.conexao import conectar_banco, fechar_banco
from utils.mensagem import mensagem_erro, mensagem_sucesso
from PySide6.QtWidgets import QFileDialog

def exportar_tabela(nome_banco, mes, ano, parent=None):
    try:
        conexao = conectar_banco(nome_banco)
        cursor = conexao.cursor()

        periodo = f"{mes}/{ano}"

        cursor.execute(f"""
            SELECT c.*, f.nome, f.cnpj
            FROM c170_clone c
            JOIN `0150` f ON f.cod_part = c.cod_part
            WHERE c.periodo = %s
        """, (periodo,))
        rows = cursor.fetchall()

        if not rows:
            mensagem_erro("Nenhum dado encontrado para o período selecionado.")
            return

        colunas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=colunas)

        for col in ['vl_item', 'resultado', 'aliquota']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('.', ',').str.replace('%', '') + '%'

        cursor.execute("SELECT cnpj FROM `0000` LIMIT 1")
        cnpj_result = cursor.fetchone()
        cursor.execute("SELECT razao_social FROM db_apuradorICMS.empresas WHERE LEFT(cnpj, 8) = LEFT(%s, 8) LIMIT 1", (cnpj_result[0],))
        nome_empresa = cursor.fetchone()[0]

        cursor.execute("SELECT dt_ini, dt_fin FROM `0000` WHERE periodo = %s LIMIT 1", (periodo,))
        dt_ini, dt_fin = cursor.fetchone()
        dt_ini_fmt = f"{dt_ini[:2]}/{dt_ini[2:4]}/{dt_ini[4:]}"
        dt_fin_fmt = f"{dt_fin[:2]}/{dt_fin[2:4]}/{dt_fin[4:]}"
        periodo_nome = f"{ano}-{mes}"

        sugestao_nome = f"{periodo_nome}-{nome_empresa}.xlsx"
        arquivo_saida, _ = QFileDialog.getSaveFileName(
            parent,
            "Salvar planilha Excel",
            sugestao_nome,
            "Planilhas Excel (*.xlsx)"
        )

        if not arquivo_saida:
            return

        with pd.ExcelWriter(arquivo_saida, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, startrow=2)
            sheet = writer.sheets['Sheet1']
            sheet['A1'] = f"{nome_empresa}"
            sheet['A2'] = f"Período: {dt_ini_fmt} a {dt_fin_fmt}"

        mensagem_sucesso(f"Exportado com sucesso para:\n{arquivo_saida}")
        cursor.close()

    except Exception as e:
        mensagem_erro(f"Erro na exportação: {e}")
    finally:
        fechar_banco(conexao)
