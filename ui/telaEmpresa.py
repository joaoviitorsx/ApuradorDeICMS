from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox
from db.empresaCRUD import listar_empresas
from ui.cadastroEmpresa import CadastroEmpresa
from ui.telaPrincipal import TelaPrincipal

class TelaEmpresa(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selecionar Empresa")
        self.setStyleSheet("background-color: #121212; color: white;")
        self.resize(400, 300)

        layout = QVBoxLayout()

        self.label = QLabel("Escolha a empresa")
        self.label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self.label)

        self.combo_empresas = QComboBox()
        self.combo_empresas.setStyleSheet("font-size: 16px; padding: 8px;")
        layout.addWidget(self.combo_empresas)

        self.btn_entrar = QPushButton("Entrar")
        self.btn_entrar.setStyleSheet("font-size: 18px; padding: 10px;")
        self.btn_entrar.clicked.connect(self.entrar_sistema)
        layout.addWidget(self.btn_entrar)

        self.btn_cadastrar = QPushButton("Cadastrar nova empresa")
        self.btn_cadastrar.setStyleSheet("font-size: 18px; padding: 10px;")
        self.btn_cadastrar.clicked.connect(self.abrir_cadastro)
        layout.addWidget(self.btn_cadastrar)

        self.setLayout(layout)
        self.atualizar_empresas()

    def atualizar_empresas(self):
        empresas = listar_empresas()
        self.combo_empresas.clear()
        self.combo_empresas.addItems(empresas)

    def abrir_cadastro(self):
        self.cadastro = CadastroEmpresa()
        self.cadastro.show()
        self.close()

    def entrar_sistema(self):
        empresa = self.combo_empresas.currentText()
        if not empresa:
            QMessageBox.warning(self, "Aviso", "Selecione uma empresa para continuar.")
            return

        self.tela_principal = TelaPrincipal(empresa)
        self.tela_principal.show()
        self.close()
