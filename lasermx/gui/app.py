"""
GUI mínima de LaserMX (PySide6)

- Combo para puertos
- Botón Conectar/Desconectar
- Botón Enviar "$H"
- Consola de log
"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QPlainTextEdit
)
from PySide6.QtCore import Qt, QTimer, Signal
from serial.tools import list_ports
from lasermx.drivers.grbl_serial import GrblSerialDriver
import sys
from typing import Optional

class MainWindow(QMainWindow):
    line_signal = Signal(str)
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LaserMX")
        self.resize(640, 480)

        self._driver: Optional[GrblSerialDriver] = None

        # UI
        central = QWidget()
        self.setCentralWidget(central)
        v = QVBoxLayout(central)

        # fila superior: puertos + conectar
        h = QHBoxLayout()
        self.lbl = QLabel("Puerto:")
        self.cmb = QComboBox()
        self.btn_refresh = QPushButton("Actualizar")
        self.btn_connect = QPushButton("Conectar")
        self.btn_home = QPushButton("Enviar $H")
        self.btn_home.setEnabled(False)

        h.addWidget(self.lbl)
        h.addWidget(self.cmb, 1)
        h.addWidget(self.btn_refresh)
        h.addWidget(self.btn_connect)
        h.addWidget(self.btn_home)
        v.addLayout(h)

        # consola
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        v.addWidget(self.log, 1)

        # señales
        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btn_connect.clicked.connect(self.toggle_connection)
        self.btn_home.clicked.connect(self.send_home)

        # carga inicial
        self.refresh_ports()

        # timer suave para autodesplazar log (evita bloqueos en callbacks)
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._autoscroll)
        self._timer.start()
        self.line_signal.connect(self._append)

    def refresh_ports(self) -> None:
        self.cmb.clear()
        for p in list_ports.comports():
            self.cmb.addItem(f"{p.device}  {p.description}", p.device)

    def _append(self, text: str) -> None:
        self.log.appendPlainText(text)

    def _on_line(self, text: str) -> None:
        # Este callback llega desde un hilo del driver: emitir señal para actualizar el UI de forma segura.
        self.line_signal.emit(text)

    def toggle_connection(self) -> None:
        if self._driver is None:
            # conectar
            dev = self.cmb.currentData()
            if not dev:
                self._append("⚠️ No hay puerto seleccionado.")
                return
            try:
                self._driver = GrblSerialDriver(on_line=self._on_line)
                self._driver.connect(dev, 115200)
                self._append(f"✅ Conectado a {dev}")
                self.btn_connect.setText("Desconectar")
                self.btn_home.setEnabled(True)
                self._driver.send_command("$H")  #enviar $H al conectar
                    
            except Exception as e:
                self._driver = None
                self._append(f"❌ Error al conectar: {e}")
        else:
            # desconectar
            try:
                self._driver.disconnect()
                self._append("🔌 Desconectado.")
            finally:
                self._driver = None
                self.btn_connect.setText("Conectar")
                self.btn_home.setEnabled(False)

    def send_home(self) -> None:
        if self._driver is None:
            self._append("⚠️ No conectado.")
            return
        try:
            self._driver.send_command("$H")
            self._append("→ $H")
        except Exception as e:
            self._append(f"❌ Error enviando $H: {e}")

    def _autoscroll(self) -> None:
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def closeEvent(self, event) -> None:
        """Asegura que la conexión serial se cierre al salir."""
        try:
            if self._driver is not None:
                self._driver.disconnect()
                self._append("🔌 Desconectado.")
        finally:
            self._driver = None
        super().closeEvent(event)

def main() -> None:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())