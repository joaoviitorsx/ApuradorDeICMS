from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from db.empresaCRUD import cadastrar_empresa, nomear_banco_por_razao_social
from ui.telaEmpresa import TelaEmpresa

import re

class CadastroEmpresa(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastro de Empresa")
        self.setStyleSheet("background-color: #030d18;")
        self.setGeometry(200, 200, 800, 600)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(20)

        titulo = QLabel("Cadastro de Nova Empresa")
        titulo.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        self.input_cnpj = QLineEdit()
        self.input_cnpj.setInputMask("##.###.###/####-##")
        self.input_cnpj.setPlaceholderText("Digite o CNPJ")
        self.input_cnpj.setStyleSheet(self.estilo_input())
        layout.addWidget(self.input_cnpj)

        self.input_razao = QLineEdit()
        self.input_razao.setPlaceholderText("Digite a razão social")
        self.input_razao.setStyleSheet(self.estilo_input())
        layout.addWidget(self.input_razao)

        btn_cadastrar = QPushButton("Cadastrar")
        btn_cadastrar.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cadastrar.setStyleSheet(self.estilo_botao())
        btn_cadastrar.clicked.connect(self.realizar_cadastro)
        layout.addWidget(btn_cadastrar)

        btn_voltar = QPushButton("Voltar")
        btn_voltar.setCursor(QCursor(Qt.PointingHandCursor))
        btn_voltar.setStyleSheet(self.estilo_botao())
        btn_voltar.clicked.connect(self.voltar_tela)
        layout.addWidget(btn_voltar)

        self.setLayout(layout)

    def estilo_input(self):
        return """
            font-size: 18px;
            padding: 10px;
            border: 1px solid #888;
            border-radius: 6px;
            background-color: white;
            color: black;
        """

    def estilo_botao(self):
        return """
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                padding: 12px 24px;
                background-color: #001F3F;
                color: #ffffff;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005588;
            }
        """

    def realizar_cadastro(self):
        cnpj = self.input_cnpj.text().strip()
        razao = self.input_razao.text().strip()

        cnpj_numeros = re.sub(r'\D', '', cnpj)
        if len(cnpj_numeros) != 14:
            QMessageBox.warning(self, "Erro", "CNPJ inválido.")
            return

        if len(razao) < 3:
            QMessageBox.warning(self, "Erro", "Razão social inválida.")
            return

        nome_banco = nomear_banco_por_razao_social(razao)
        if re.match(r'^[\d_]', nome_banco):
            QMessageBox.warning(self, "Erro", "Nome do banco não pode começar com número ou underline.")
            return

        if not re.match(r'^[a-zA-Z0-9_]+$', nome_banco):
            QMessageBox.warning(self, "Erro", "Nome do banco só pode conter letras, números e underline.")
            return

        try:
            cadastrar_empresa(cnpj_numeros, razao)
            QMessageBox.information(self, "Sucesso", f"Empresa '{razao}' cadastrada com sucesso!")
            self.voltar_tela()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao cadastrar a empresa:\n{e}")

    def voltar_tela(self):
        self.tela_empresa = TelaEmpresa()
        self.tela_empresa.showMaximized()
        self.close()
