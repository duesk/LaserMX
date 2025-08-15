from PySide6 import QtWidgets
import sys
from .gui.main_window import MainWindow
from .utils.logging_setup import setup_logging

def main():
    setup_logging("INFO")
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())