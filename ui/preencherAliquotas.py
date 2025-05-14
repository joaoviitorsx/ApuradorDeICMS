from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,QPushButton, QMessageBox, QHeaderView
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from db.conexao import conectar_banco, fechar_banco

class PreencherAliquotas(QWidget):
    def __init__(self, nome_banco_empresa):
        super().__init__()
        self.nome_banco = nome_banco_empresa
        self.setWindowTitle("Preencher Alíquotas")
        self.setStyleSheet("background-color: #030d18; color: white;")
        self.setGeometry(200, 100, 1000, 600)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Código", "Produto", "NCM", "Alíquota"])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setStyleSheet("background-color: white; color: black; font-size: 14px;")
        layout.addWidget(self.tabela)

        self.btn_salvar = QPushButton("Salvar Tudo")
        self.btn_salvar.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_salvar.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                padding: 10px;
                background-color: #001F3F;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #005588;
            }
        """)
        self.btn_salvar.clicked.connect(self.salvar_aliquotas)
        layout.addWidget(self.btn_salvar, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.carregar_dados()

    def carregar_dados(self):
        conexao = conectar_banco(self.nome_banco)
        try:
            cursor = conexao.cursor()
            cursor.execute("""
                SELECT codigo, produto, ncm, aliquota
                FROM cadastro_tributacao
                WHERE aliquota IS NULL OR aliquota = ''
            """)
            resultados = cursor.fetchall()

            self.tabela.setRowCount(len(resultados))
            for linha_idx, linha in enumerate(resultados):
                for col_idx, valor in enumerate(linha):
                    item = QTableWidgetItem(str(valor) if valor else "")
                    if col_idx == 3:
                        item.setFlags(item.flags() | Qt.ItemIsEditable)
                    else:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.tabela.setItem(linha_idx, col_idx, item)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar os dados: {e}")
        finally:
            fechar_banco(conexao)

    def salvar_aliquotas(self):
        linhas = self.tabela.rowCount()
        atualizacoes = []

        for linha in range(linhas):
            codigo = self.tabela.item(linha, 0).text().strip()
            aliquota = self.tabela.item(linha, 3).text().strip()
            if aliquota:
                atualizacoes.append((aliquota, codigo))

        if not atualizacoes:
            QMessageBox.information(self, "Aviso", "Nenhuma alíquota preenchida.")
            return

        conexao = conectar_banco(self.nome_banco)
        try:
            cursor = conexao.cursor()
            cursor.executemany("""
                UPDATE cadastro_tributacao
                SET aliquota = %s
                WHERE codigo = %s
            """, atualizacoes)
            conexao.commit()

            QMessageBox.information(self, "Sucesso", f"{len(atualizacoes)} alíquotas salvas com sucesso.")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")
        finally:
            fechar_banco(conexao)
