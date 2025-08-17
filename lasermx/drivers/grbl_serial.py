"""
Driver serial GRBL (no bloqueante) para LaserMX.

- Conecta/desconecta
- Envía líneas de G-code/comandos
- Lee respuestas en un hilo y las pasa a un callback
"""
from __future__ import annotations
import threading
import time
from typing import Optional, Callable
import serial

class GrblSerialDriver:
    def __init__(self, on_line: Optional[Callable[[str], None]] = None):
        self.on_line = on_line or (lambda s: None)
        self._ser: Optional[serial.Serial] = None
        self._rx_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def connect(self, port: str, baud: int = 115200, timeout: float = 1.0) -> None:
        self._ser = serial.Serial(port, baudrate=baud, timeout=timeout)
        self._stop.clear()
        # hilo de lectura
        self._rx_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._rx_thread.start()
        # limpia banner inicial de GRBL si aparece
        time.sleep(0.1)
        self._drain()

    def _drain(self) -> None:
        if not self._ser:
            return
        try:
            while self._ser.in_waiting:
                line = self._ser.readline().decode(errors="ignore").strip()
                if line:
                    self.on_line(line)
        except Exception:
            pass

    def _reader_loop(self) -> None:
        assert self._ser is not None
        while not self._stop.is_set():
            try:
                line = self._ser.readline().decode(errors="ignore").strip()
                if line:
                    self.on_line(line)
            except Exception:
                break

    def send_command(self, line: str) -> None:
        if not self._ser:
            raise RuntimeError("No conectado")
        data = (line.strip() + "\n").encode("ascii", errors="ignore")
        self._ser.write(data)
        self._ser.flush()

    def disconnect(self) -> None:
        self._stop.set()
        if self._rx_thread and self._rx_thread.is_alive():
            self._rx_thread.join(timeout=1.0)
        if self._ser:
            try:
                self._ser.close()
            finally:
                self._ser = None