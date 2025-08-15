from typing import List
from serial.tools import list_ports

def list_serial_ports() -> List[str]:
    return [p.device for p in list_ports.comports()]
