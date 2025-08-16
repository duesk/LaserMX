
LaserMX
=======

LaserMX es un software open source, escrito en español, para controlar máquinas láser
compatibles con GRBL. Su primera versión está enfocada en macOS (Apple Silicon).

Características v0.1
--------------------
- Conexión a puerto serial y envío de comandos GRBL.
- Carga de archivos SVG/DXF sencillos.
- Conversión a trayectorias G-code (G0/G1, M3/M5).
- Interfaz gráfica simple con PySide6: selección de puerto, conexión, envío de comandos,
  carga de archivo y vista previa 2D básica.

Instalación (macOS)
-------------------
1. Crear entorno virtual:
   python3 -m venv .venv
   source .venv/bin/activate

2. Instalar dependencias:
   python -m pip install -U pip setuptools wheel
   python -m pip install -e . --config-settings editable_mode=compat

Uso rápido
----------
CLI:
    lasermx --list
    lasermx --port /dev/tty.usbserial-1410 --cmd "$H"
    lasermx --file examples/simple_square.svg --to-gcode out.gcode --run

GUI:
    lasermx-gui

Comandos GRBL comunes
---------------------
- $H             -> homing
- M3 S1000       -> encender láser con potencia S
- M5             -> apagar láser
- G0 X10 Y10     -> movimiento rápido
- G1 X20 Y20 F500 -> corte con feedrate

Ejemplo mínimo en Python
------------------------
from lasermx.drivers.grbl_serial import GrblSerialDriver

drv = GrblSerialDriver(on_line=print)
drv.connect("/dev/tty.usbserial-1410", 115200)
drv.send_command("$I")
drv.disconnect()

Roadmap futuro
--------------
- Vista 2D/3D avanzada y simulación de trayectorias.
- Plugins de importación (AI, PDF, imágenes vectoriales).
- Soporte multiplataforma (Windows).
- Comunidad y guías de contribución.
