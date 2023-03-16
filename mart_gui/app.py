import sys
from PyQt6.QtWidgets import QApplication
from .main_window import MainUi


def create_qt_ui(args):
    app = QApplication(args)
    create_qt_ui.window = MainUi()
    app.exec()


def main():
    create_qt_ui(sys.argv)

