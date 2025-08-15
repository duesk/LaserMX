from __future__ import annotations
from typing import List, Tuple, Iterable

Point = Tuple[float, float]
Polyline = List[Point]

def polylines_to_gcode(polys: List[Polyline], feed: float = 1000.0, power_s: int = 1000) -> List[str]:
    g: List[str] = ["G90", "G21"]  # absoluto, mm
    for pts in polys:
        if not pts: continue
        x0, y0 = pts[0]
        g.append(f"G0 X{x0:.3f} Y{y0:.3f}")
        g.append(f"M3 S{power_s}")
        last = (x0, y0)
        for x, y in pts[1:]:
            if (x, y) != last:
                g.append(f"G1 X{x:.3f} Y{y:.3f} F{feed:.2f}")
                last = (x, y)
        g.append("M5")
    return g

def save_gcode(lines: Iterable[str], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln.rstrip() + "\n")
            