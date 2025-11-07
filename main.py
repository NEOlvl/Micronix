# Короткий входной файл, запускающий PyQt6 GUI
# Запуск: python main.py
import sys
from PyQt6.QtWidgets import QApplication
from micronix_ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()