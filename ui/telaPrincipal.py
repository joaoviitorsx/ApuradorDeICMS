import asyncio

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton,QHBoxLayout, QMessageBox, QFileDialog, QComboBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QFont

from datetime import datetime
from utils.mensagem import mensagem_erro, mensagem_aviso, mensagem_sucesso
from utils.process_data import process_data
from utils.verificacoes import verificar_aliquotas_nulas
from services.tributacao_service import importar_planilha_tributacao
from services.sped_service import processar_sped, atualizar_ncm, clonar_c170,atualizar_aliquota, atualizar_aliquota_simples, atualizar_resultado
from services.exportacaoService import exportar_tabela
from services.fornecedor_service import cadastro_fornecedores

class TelaPrincipal(QWidget):
    def __init__(self, nome_empresa):
        super().__init__()
        self.nome_empresa = nome_empresa
        self.setWindowTitle(f"Apurador de ICMS - {self.nome_empresa}")
        self.setStyleSheet("background-color: #030d18;")
        self.setGeometry(100, 100, 900, 700)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)

        titulo = QLabel(f"Empresa Selecionada: {self.nome_empresa}")
        titulo.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        botoes = [
            ("📄 Enviar Tributação", self.enviar_tributacao),
            ("📥 Importar SPED", self.importar_sped),
            ("📤 Exportar por Mês/Ano", self.exportar_tabela),
            ("🔙 Voltar ao Início", self.voltar)
        ]

        for texto, acao in botoes:
            btn = QPushButton(texto)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet(self.estilo_botao())
            btn.setMinimumHeight(50)
            btn.clicked.connect(acao)
            layout.addWidget(btn)

        layout.addStretch()
        self.setLayout(layout)

        linha_export = QHBoxLayout()

        self.combo_mes = QComboBox()
        self.combo_mes.addItems(["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"])
        self.combo_mes.setStyleSheet("font-size: 16px; padding: 5px; background-color: white; color: black;")
        linha_export.addWidget(self.combo_mes)

        self.combo_ano = QComboBox()
        ano_atual = datetime.now().year
        self.combo_ano.addItems([str(ano_atual - 2), str(ano_atual - 1), str(ano_atual), str(ano_atual + 1)])
        self.combo_ano.setStyleSheet("font-size: 16px; padding: 5px; background-color: white; color: black;")
        linha_export.addWidget(self.combo_ano)

        self.btn_exportar = QPushButton("📤 Exportar Tabela")
        self.btn_exportar.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_exportar.setStyleSheet(self.estilo_botao())
        self.btn_exportar.clicked.connect(self.exportar_tabela)
        linha_export.addWidget(self.btn_exportar)

        layout.addLayout(linha_export)

    def estilo_botao(self):
        return """
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                padding: 14px;
                background-color: #001F3F;
                color: #ffffff;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #005588;
            }
        """

    def enviar_tributacao(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Planilha de Tributação",
            "",
            "Planilhas Excel (*.xlsx)"
        )
        if not caminho:
            return
        importar_planilha_tributacao(caminho, self.nome_empresa)

    def importar_sped(self):
        arquivos, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Arquivos SPED",
            "",
            "Arquivos Texto (*.txt)"
        )

        if not arquivos:
            return

        try:
            for i, caminho in enumerate(arquivos):
                with open(caminho, 'r', encoding='utf-8', errors='ignore') as arquivo:
                    conteudo = arquivo.read()
                    from db.empresaCRUD import nomear_banco_por_razao_social

                    nome_banco = nomear_banco_por_razao_social(self.nome_empresa)
                    processar_sped(conteudo, nome_banco)

            atualizar_ncm(self.nome_empresa)
            clonar_c170(self.nome_empresa)
            atualizar_aliquota(self.nome_empresa)
            atualizar_aliquota_simples(self.nome_empresa)
            atualizar_resultado(self.nome_empresa)
            cadastro_fornecedores(self.nome_empresa)

            mensagem_sucesso(f"{len(arquivos)} arquivo(s) SPED processado(s) com sucesso.")
            verificar_aliquotas_nulas(self.nome_empresa, self)

        except Exception as e:
            mensagem_erro(f"Erro ao importar SPED: {e}")

    def exportar_tabela(self):
        mes = self.combo_mes.currentText()
        ano = self.combo_ano.currentText()

        if not mes or not ano:
            from utils.mensagem import mensagem_erro
            mensagem_erro("Selecione o mês e o ano para exportação.")
            return

        exportar_tabela(self.nome_empresa, mes, ano, self)


    def voltar(self):
        from ui.telaEmpresa import TelaEmpresa
        self.inicio = TelaEmpresa()
        self.inicio.showMaximized()
        self.close()
