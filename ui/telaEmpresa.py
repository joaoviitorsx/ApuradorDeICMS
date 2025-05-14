from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox,QPushButton, QMessageBox, QSpacerItem, QSizePolicy
from PySide6.QtGui import QFont, QCursor
from PySide6.QtCore import Qt

from db.empresaCRUD import listar_empresas
from ui.cadastroEmpresa import CadastroEmpresa  # import futuro
# from ui.telaPrincipal import TelaPrincipal  # substitua pelo real

class TelaEmpresa(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apurador de ICMS - Escolha a Empresa")
        self.setStyleSheet("background-color: #030d18;")
        self.setGeometry(100, 100, 800, 600)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        titulo = QLabel("Selecione ou Cadastre uma Empresa")
        titulo.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.combo_empresas = QComboBox()
        self.combo_empresas.setStyleSheet("""
            QComboBox {
                font-size: 18px;
                padding: 10px;
                border: 1px solid #888;
                border-radius: 6px;
                background-color: #001F3F;
                color: white;
            }
            QComboBox QAbstractItemView {
                background-color: #001F3F;
                selection-background-color: #005588;
                color: white;
            }
        """)
        self.carregar_empresas()
        layout.addWidget(self.combo_empresas, alignment=Qt.AlignCenter)

        btn_entrar = QPushButton("Entrar")
        btn_entrar.setCursor(QCursor(Qt.PointingHandCursor))
        btn_entrar.setStyleSheet(self.estilo_botao())
        btn_entrar.clicked.connect(self.entrar_sistema)
        layout.addWidget(btn_entrar, alignment=Qt.AlignCenter)

        btn_cadastrar = QPushButton("Cadastrar Empresa")
        btn_cadastrar.setCursor(QCursor(Qt.PointingHandCursor))
        btn_cadastrar.setStyleSheet(self.estilo_botao())
        btn_cadastrar.clicked.connect(self.abrir_cadastro)
        layout.addWidget(btn_cadastrar, alignment=Qt.AlignCenter)

        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(layout)

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

    def carregar_empresas(self):
        empresas = listar_empresas()
        self.combo_empresas.clear()
        self.combo_empresas.addItem("Selecione uma empresa")
        self.combo_empresas.model().item(0).setEnabled(False)
        self.combo_empresas.addItems(empresas)

    def entrar_sistema(self):
        nome_empresa = self.combo_empresas.currentText()
        if nome_empresa == "Selecione uma empresa":
            QMessageBox.warning(self, "Aviso", "Selecione uma empresa para continuar.")
            return

        # Aqui você redirecionaria para a próxima tela (ainda a ser criada)
        # self.tela_principal = TelaPrincipal(nome_empresa)
        # self.tela_principal.showMaximized()
        self.close()
        print(f">>> Entrando no sistema da empresa: {nome_empresa}")

    def abrir_cadastro(self):
        self.cadastro = CadastroEmpresa()
        self.cadastro.showMaximized()
        self.close()
