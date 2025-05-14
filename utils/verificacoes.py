from PySide6.QtWidgets import QMessageBox
from db.conexao import conectar_banco, fechar_banco
from ui.preencherAliquotas import PreencherAliquotas

def verificar_aliquotas_nulas(nome_banco, parent=None):
    conexao = conectar_banco(nome_banco)
    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM cadastro_tributacao
            WHERE aliquota IS NULL OR aliquota = ''
        """)
        resultado = cursor.fetchone()
        total_nulas = resultado['total'] if resultado else 0

        if total_nulas == 0:
            return  # Nada a fazer

        # Exibir popup ao usuário
        resposta = QMessageBox.question(
            parent,
            "Alíquotas Pendentes",
            f"Há {total_nulas} produtos com alíquota não informada.\nDeseja preenchê-las agora?",
            QMessageBox.Yes | QMessageBox.No
        )

        if resposta == QMessageBox.Yes:
            tela = PreencherAliquotas(nome_banco)
            tela.showMaximized()

    except Exception as e:
        QMessageBox.critical(parent, "Erro", f"Erro ao verificar alíquotas: {e}")
    finally:
        fechar_banco(conexao)
