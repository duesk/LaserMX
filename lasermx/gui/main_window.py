from __future__ import annotations
from PySide6 import QtWidgets, QtCore, QtGui
from typing import List
from ..drivers.grbl_serial import GrblSerialDriver
from ..utils.serial_utils import list_serial_ports
from ..pipeline.svg_loader import load_svg_as_polylines
from ..pipeline.dxf_loader import load_dxf_as_polylines
from ..pipeline.gcode_generator import polylines_to_gcode, save_gcode

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LaserMX v0.1")
        self.resize(900, 600)
        self.driver = GrblSerialDriver(on_line=self._on_grbl_line)

        central = QtWidgets.QWidget(); self.setCentralWidget(central)
        layout = QtWidgets.QGridLayout(central)

        self.port_combo = QtWidgets.QComboBox()
        self.refresh_btn = QtWidgets.QPushButton("Actualizar puertos")
        self.connect_btn = QtWidgets.QPushButton("Conectar")
        self.cmd_edit = QtWidgets.QLineEdit(); self.cmd_edit.setPlaceholderText("Comando GRBL (ej. $I, $H, M3 S1000)")
        self.send_btn = QtWidgets.QPushButton("Enviar")
        self.load_btn = QtWidgets.QPushButton("Cargar SVG/DXF")
        self.save_btn = QtWidgets.QPushButton("Guardar G-code")
        self.run_btn = QtWidgets.QPushButton("Enviar G-code")

        self.log = QtWidgets.QPlainTextEdit(); self.log.setReadOnly(True)
        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.scene); self.view.setRenderHints(QtGui.QPainter.Antialiasing)

        layout.addWidget(self.port_combo, 0, 0)
        layout.addWidget(self.refresh_btn, 0, 1)
        layout.addWidget(self.connect_btn, 0, 2)
        layout.addWidget(self.cmd_edit, 1, 0, 1, 2)
        layout.addWidget(self.send_btn, 1, 2)
        layout.addWidget(self.load_btn, 2, 0)
        layout.addWidget(self.save_btn, 2, 1)
        layout.addWidget(self.run_btn, 2, 2)
        layout.addWidget(self.view, 3, 0, 1, 3)
        layout.addWidget(self.log, 4, 0, 1, 3)

        self.current_polys: List[List[tuple[float,float]]] = []

        self.refresh_btn.clicked.connect(self._refresh_ports)
        self.connect_btn.clicked.connect(self._toggle_connection)
        self.send_btn.clicked.connect(self._send_cmd)
        self.load_btn.clicked.connect(self._load_file)
        self.save_btn.clicked.connect(self._save_gcode)
        self.run_btn.clicked.connect(self._run_gcode)

        self._refresh_ports()

    def _refresh_ports(self):
        self.port_combo.clear()
        for p in list_serial_ports():
            self.port_combo.addItem(p)

    def _toggle_connection(self):
        if self.connect_btn.text() == "Conectar":
            port = self.port_combo.currentText()
            try:
                self.driver.connect(port, 115200)
                self.connect_btn.setText("Desconectar")
                self._log(f"Conectado a {port}")
                self.driver.send_command("$$")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))
        else:
            self.driver.disconnect()
            self.connect_btn.setText("Conectar")
            self._log("Desconectado.")

    def _send_cmd(self):
        cmd = self.cmd_edit.text().strip()
        if not cmd: return
        try:
            self.driver.send_command(cmd)
            self._log(f">> {cmd}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def _load_file(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Cargar archivo", "", "Vectores (*.svg *.dxf)")
        if not fn: return
        if fn.lower().endswith(".svg"):
            self.current_polys = load_svg_as_polylines(fn)
        else:
            self.current_polys = load_dxf_as_polylines(fn)
        self._draw_preview(self.current_polys)
        self._log(f"Cargado: {fn} ({sum(len(p) for p in self.current_polys)} puntos)")

    def _save_gcode(self):
        if not self.current_polys:
            QtWidgets.QMessageBox.information(self, "Aviso", "No hay trayectorias cargadas.")
            return
        out, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar G-code", "out.gcode", "G-code (*.gcode *.nc *.txt)")
        if not out: return
        g = polylines_to_gcode(self.current_polys, feed=1000.0, power_s=1000)
        save_gcode(g, out)
        self._log(f"G-code guardado en {out}")

    def _run_gcode(self):
        if not self.current_polys:
            QtWidgets.QMessageBox.information(self, "Aviso", "No hay trayectorias cargadas.")
            return
        try:
            g = polylines_to_gcode(self.current_polys, feed=1000.0, power_s=800)
            self.driver.stream_gcode(g, delay=0.0)
            self._log("G-code enviado al controlador.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def _draw_preview(self, polys):
        self.scene.clear()
        pen = QtGui.QPen()
        for pts in polys:
            path = QtGui.QPainterPath()
            if not pts: continue
            x0, y0 = pts[0]
            path.moveTo(x0, -y0)
            for x, y in pts[1:]:
                path.lineTo(x, -y)   # invertimos Y para vista cartesiana
            self.scene.addPath(path, pen)
        self.view.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)

    def _on_grbl_line(self, text: str):
        self._log(text)

    def _log(self, msg: str):
        self.log.appendPlainText(msg)