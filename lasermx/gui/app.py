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

try:
    from lasermx.drivers.fake_grbl import FakeGrblDriver  # nuevo módulo externo
except Exception:
    FakeGrblDriver = None  # type: ignore

class MainWindow(QMainWindow):
    line_signal = Signal(str)
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LaserMX")
        self.resize(640, 480)

        self._driver: Optional[GrblSerialDriver] = None
        self._homing_in_progress: bool = False
        self._last_cmd: str | None = None
        self._is_fake: bool = False
        self._homing_timer = QTimer(self)
        self._homing_timer.setSingleShot(True)
        self._homing_timer.timeout.connect(self._complete_homing)

        # UI
        central = QWidget()
        self.setCentralWidget(central)
        v = QVBoxLayout(central)

        # fila superior: puertos + conectar
        h = QHBoxLayout()
        self.lbl = QLabel("Puerto:")
        self.cmb = QComboBox()
        self.lbl_baud = QLabel("Baudios:")
        self.cmb_baud = QComboBox()
        for b in (9600, 19200, 38400, 57600, 115200, 250000):
            self.cmb_baud.addItem(str(b), b)
        # Seleccionar 115200 por defecto si existe
        idx_115200 = self.cmb_baud.findText("115200")
        if idx_115200 >= 0:
            self.cmb_baud.setCurrentIndex(idx_115200)
        self.btn_refresh = QPushButton("Actualizar")
        self.btn_connect = QPushButton("Conectar")
        self.btn_home = QPushButton("Enviar $H")
        self.btn_home.setEnabled(False)

        h.addWidget(self.lbl)
        h.addWidget(self.cmb, 1)
        h.addWidget(self.lbl_baud)
        h.addWidget(self.cmb_baud)
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
        # Opción simulada solo si el módulo está disponible
        if FakeGrblDriver is not None:
            self.cmb.addItem("FAKE (simulador)", "__FAKE__")
        for p in list_ports.comports():
            self.cmb.addItem(f"{p.device}  {p.description}", p.device)

    def _append(self, text: str) -> None:
        self.log.appendPlainText(text)
        # Si estamos en homing, re-habilitar el botón al recibir confirmación
        t = (text or "").strip().lower()
        if self._homing_in_progress:
            if t == "ok" and (self._last_cmd or "").lower() == "$h":
                self._complete_homing()
            elif t.startswith("error"):
                # En caso de error, permitir reintentar
                self._complete_homing()
            elif self._is_fake and "[homing|pull-off]" in t:
                # En el driver FAKE, la etapa Pull-off indica que el ok vendrá enseguida.
                # Arranca un temporizador corto como tolerancia por si el 'ok' se pierde.
                if not self._homing_timer.isActive():
                    self._homing_timer.start(400)

    def _complete_homing(self) -> None:
        """Finaliza el estado de homing y habilita el botón."""
        self._homing_in_progress = False
        self._last_cmd = None
        self.btn_home.setEnabled(True)

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
            # Bloquear selectores durante la conexión
            self.cmb.setEnabled(False)
            self.btn_refresh.setEnabled(False)
            self.cmb_baud.setEnabled(False)
            try:
                if dev == "__FAKE__":
                    if FakeGrblDriver is None:
                        self._append("⚠️ Modo FAKE no disponible (módulo faltante).")
                        return
                    self._driver = FakeGrblDriver(on_line=self._on_line)
                else:
                    self._driver = GrblSerialDriver(on_line=self._on_line)
                self._is_fake = (dev == "__FAKE__")
                # Obtener baudios del selector
                try:
                    baud = int(self.cmb_baud.currentData() or self.cmb_baud.currentText())
                except Exception:
                    baud = 115200
                self._driver.connect(dev, baud)
                # Mantener bloqueados al estar conectados
                self.cmb.setEnabled(False)
                self.btn_refresh.setEnabled(False)
                self.cmb_baud.setEnabled(False)
                self._append(f"✅ Conectado a {dev}")
                self.btn_connect.setText("Desconectar")
                self.btn_home.setEnabled(True)
                # Enviar $H automáticamente y deshabilitar botón mientras dura
                self._homing_in_progress = True
                self._last_cmd = "$h"
                self.btn_home.setEnabled(False)
                self._driver.send_command("$H")
                if self._is_fake and not self._homing_timer.isActive():
                    # Fallback por si no llega el 'ok' del simulador
                    self._homing_timer.start(1500)
                    
            except Exception as e:
                # Rehabilitar si falló la conexión
                self.cmb.setEnabled(True)
                self.btn_refresh.setEnabled(True)
                self.cmb_baud.setEnabled(True)
                self._driver = None
                self._append(f"❌ Error al conectar: {e}")
        else:
            # desconectar
            try:
                self._driver.disconnect()
                self._append("🔌 Desconectado.")
            finally:
                self._driver = None
                # Rehabilitar selectores al desconectar
                self.cmb.setEnabled(True)
                self.btn_refresh.setEnabled(True)
                self.cmb_baud.setEnabled(True)
                self.btn_connect.setText("Conectar")
                self.btn_home.setEnabled(False)

    def send_home(self) -> None:
        if self._driver is None:
            self._append("⚠️ No conectado.")
            return
        if self._homing_in_progress:
            self._append("⚠️ Ya hay un homing en progreso.")
            return
        try:
            self._homing_in_progress = True
            self._last_cmd = "$h"
            self.btn_home.setEnabled(False)
            self._driver.send_command("$H")
            if self._is_fake and not self._homing_timer.isActive():
                self._homing_timer.start(1500)
            self._append("→ $H")
        except Exception as e:
            self._homing_in_progress = False
            self._last_cmd = None
            self.btn_home.setEnabled(True)
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
        # Reset de estados por si se cierra durante homing
        self._homing_in_progress = False
        self._last_cmd = None
        if self._homing_timer.isActive():
            self._homing_timer.stop()
        self.btn_home.setEnabled(False)
        super().closeEvent(event)

def main() -> None:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())