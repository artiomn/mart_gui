#!/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication
from src.main_window import MainUi


def create_qt_ui(args):
    app = QApplication(args)
    create_qt_ui.window = MainUi()
    app.exec()


create_qt_ui(sys.argv)
