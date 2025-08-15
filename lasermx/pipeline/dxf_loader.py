from __future__ import annotations
from typing import List, Tuple
import ezdxf

Point = Tuple[float, float]
Polyline = List[Point]

def load_dxf_as_polylines(path: str) -> List[Polyline]:
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    polylines: List[Polyline] = []
    for e in msp:
        if e.dxftype() == "LINE":
            polylines.append([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
        elif e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
            pts = [(p[0], p[1]) for p in e.get_points()]
            polylines.append(pts)
        elif e.dxftype() == "SPLINE":
            pts = [(p[0], p[1]) for p in e.approximate(100)]
            polylines.append(pts)
    return polylines