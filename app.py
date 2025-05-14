import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from ui.dashboard import Dashboard
from utils.icone import usar_icone, recurso_caminho

def main():
    app = QApplication(sys.argv)

    usar_icone(app)

    qss_path = recurso_caminho("styles/main.qss")
    with open(qss_path, "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())

    janela = Dashboard()
    janela.showMaximized()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
