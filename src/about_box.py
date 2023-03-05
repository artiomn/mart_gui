from pathlib import Path
from sys import version as python_version

from PyQt6 import uic
from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR

from markdown_toolset.__version__ import __version__ as mt_version


class AboutBox(QDialog):
    def __init__(self):
        super(AboutBox, self).__init__()
        uic.loadUi(Path(__file__).parent / 'resources' / 'about.ui', self)
        self.label_prog_version.setText('0.1')
        self.label_md_toolkit_version.setText(mt_version)
        self.label_python_version.setText(python_version)
        self.label_qt_version.setText(QT_VERSION_STR)
        self.label_pyqt_version.setText(PYQT_VERSION_STR)

        self.exec()