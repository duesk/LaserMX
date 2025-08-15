# LaserMX

**LaserMX** es un software de control de corte láser, 100% documentado en español y desarrollado como proyecto **open source latino**, inicialmente para macOS (ARM/M1/M2) y compatible con firmware **GRBL**.

## ✨ Características iniciales
- Conexión a máquinas láser mediante **puerto serial**.
- Envío de **comandos básicos de movimiento y corte**.
- Carga de archivos **SVG/DXF** sencillos y conversión a trayectorias GRBL.
- Interfaz gráfica simple usando **PyQt6** (optimizada para macOS).
- Arquitectura modular para facilitar la extensión del software.

## 📦 Instalación en macOS
1. Clona este repositorio:
   ```bash
   git clone https://github.com/duesk/LaserMX.git
   cd LaserMX
   ```
2. Crea y activa un entorno virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## 🔌 Conexión a una máquina GRBL
1. Conecta tu máquina láser por USB.
2. Identifica el puerto:
   ```bash
   ls /dev/tty.*
   ```
3. Ejecuta LaserMX y selecciona el puerto correspondiente.

## 🖥 Ejemplo de uso
```bash
python lasermx.py
```
Luego, desde la interfaz, selecciona el archivo SVG/DXF y envíalo a la máquina.

## 📌 Próximos pasos
- Visualización 2D/3D de trayectorias.
- Soporte para más formatos de archivo.
- Comunidad de contribuidores y documentación colaborativa.

---

💡 **Inspirado en**: [Rayforge](https://github.com/barebaric/rayforge) pero con un enfoque simplificado, optimizado y documentado 100% en español.
