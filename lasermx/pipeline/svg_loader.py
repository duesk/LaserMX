from __future__ import annotations
from typing import List, Tuple
from svgpathtools import svg2paths2

Point = Tuple[float, float]
Polyline = List[Point]

def load_svg_as_polylines(path: str, samples_per_curve: int = 50) -> List[Polyline]:
    paths, attrs, svg_attr = svg2paths2(path)
    polylines: List[Polyline] = []
    for p in paths:
        pts: List[Point] = []
        length = p.length(error=1e-4)
        n = max(2, min(1000, int(samples_per_curve * (length + 1e-6))))
        for i in range(n + 1):
            t = i / n
            z = p.point(t)
            pts.append((z.real, z.imag))
        polylines.append(pts)
    return polylines