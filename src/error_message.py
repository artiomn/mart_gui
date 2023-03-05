from PyQt6.QtWidgets import QMessageBox, QWidget


class ErrorMessage(QMessageBox):
    """
    Show MessageBox with error message.
    """

    def __init__(self, w: QWidget, e):
        super().__init__()
        self.setInformativeText(e)
        self.critical(w, self.tr('Error'), e)
