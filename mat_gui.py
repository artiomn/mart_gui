#!/bin/env python3
import logging
import sys
from io import StringIO
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QAbstractItemView

from PyQt6.QtWidgets import QApplication

from src.ui_classes import MainUi


def create_qt_ui(args):
    app = QApplication(args)

    window = MainUi()

    app.exec()


create_qt_ui(sys.argv)
