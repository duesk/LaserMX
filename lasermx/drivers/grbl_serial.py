import serial, threading, time
from typing import Optional, Callable, Iterable, List
from serial.tools import list_ports

def list_serial_ports() -> List[str]:
    return [p.device for p in list_ports.comports()]

class GrblSerialDriver:
    def __init__(self, on_line: Optional[Callable[[str], None]] = None, timeout: float = 0.1):
        self._ser = None
        self._reader = None
        self._stop = threading.Event()
        self.on_line = on_line
        self.timeout = timeout

    def connect(self, port: str, baudrate: int = 115200):
        self._ser = serial.Serial(port, baudrate=baudrate, timeout=self.timeout)
        self._stop.clear()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        time.sleep(0.1)
        self._ser.reset_input_buffer()

    def disconnect(self):
        self._stop.set()
        if self._reader and self._reader.is_alive():
            self._reader.join(timeout=1.0)
        if self._ser:
            self._ser.close()
            self._ser = None

    def send_command(self, cmd: str):
        if not self._ser or not self._ser.is_open:
            raise RuntimeError("No hay conexión abierta.")
        self._ser.write((cmd.strip() + "\n").encode("ascii"))

    def _read_loop(self):
        buf = b""
        while not self._stop.is_set():
            chunk = self._ser.read(256)
            if not chunk:
                continue
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                text = line.decode(errors="ignore").strip()
                if self.on_line:
                    self.on_line(text)