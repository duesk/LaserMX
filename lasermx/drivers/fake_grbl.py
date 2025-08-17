"""
Driver simulado de GRBL para pruebas sin hardware.

API compatible con GrblSerialDriver (subset):
- __init__(on_line: Callable[[str], None])
- connect(port: str, baud: int = 115200) -> None
- send_command(cmd: str) -> None
- disconnect() -> None
"""

from __future__ import annotations
import threading
import time
import queue
from typing import Callable, Optional

class FakeGrblDriver:
    def __init__(self, on_line: Callable[[str], None]):
        self._on_line = on_line
        self._alive = False
        self._q: "queue.Queue[str]" = queue.Queue()
        self._thr: Optional[threading.Thread] = None

    def connect(self, port: str, baud: int = 115200) -> None:
        # port/baud ignorados en modo fake
        if self._alive:
            return
        self._alive = True
        self._thr = threading.Thread(target=self._worker, daemon=True)
        self._thr.start()
        # Banner típico de GRBL
        self._on_line("Grbl 1.1h ['$' for help]")

    def send_command(self, cmd: str) -> None:
        if not self._alive:
            raise RuntimeError("FakeGrblDriver: no conectado")
        self._q.put(cmd.strip())

    def disconnect(self) -> None:
        self._alive = False
        try:
            self._q.put_nowait("__STOP__")
        except Exception:
            pass
        if self._thr and self._thr.is_alive():
            self._thr.join(timeout=0.5)
        self._thr = None

    # --- hilo de procesamiento ---
    def _worker(self) -> None:
        status_counter = 0
        while self._alive:
            try:
                cmd = self._q.get(timeout=0.1)
            except queue.Empty:
                continue
            if cmd == "__STOP__":
                break

            if cmd == "?":
                state = "Run" if (status_counter % 10) >= 5 else "Idle"
                self._on_line(f"<{state}|MPos:0.000,0.000,0.000|FS:0,0>")
                status_counter += 1
                continue

            if cmd == "$":
                self._on_line("$0=10  (step pulse, usec)")
                self._on_line("$1=25  (step idle delay, msec)")
                self._on_line("$10=1  (status report mask)")
                self._on_line("ok")
                continue

            if cmd == "$$":
                self._on_line("$0=10")
                self._on_line("$1=25")
                self._on_line("$100=80.000 (x, step/mm)")
                self._on_line("$101=80.000 (y, step/mm)")
                self._on_line("$102=400.000 (z, step/mm)")
                self._on_line("ok")
                continue

            if cmd == "$I":
                self._on_line("[MSG:LaserMX Fake Driver]")
                self._on_line("[VER:1.1h.2025:FAKE]")
                self._on_line("ok")
                continue

            if cmd == "$H":
                self._on_line("[Homing|Start]")
                time.sleep(0.2)
                self._on_line("[Homing|Seek]")
                time.sleep(0.2)
                self._on_line("[Homing|Pull-off]")
                time.sleep(0.2)
                self._on_line("ok")
                continue

            if cmd.upper().startswith(("G0", "G1", "G90", "G91", "F", "M3", "M5")):
                self._on_line("ok")
                continue

            self._on_line("error: Unsupported command in FAKE mode")