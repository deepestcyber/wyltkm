"""Bounding box of what an SVG actually draws.

Icons do not always stay inside their viewBox (Font Awesome 7 draws parts
outside it), so placing them by the viewBox alone lets them overflow. This
module computes a box that contains all drawn paths, with transforms applied.
Curves and arcs are sampled (16 points each), which is tight; it may miss
the outermost bit of a curve by a hair, far less than the half-module
margin around the icon.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET

Matrix = tuple[float, float, float, float, float, float]  # a b c d e f
IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

_TOKEN = re.compile(r"[A-Za-z]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


def _mul(m: Matrix, n: Matrix) -> Matrix:
    """m × n: apply n first, then m."""
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2,
            a * e2 + c * f2 + e, b * e2 + d * f2 + f)


def parse_transform(text: str | None) -> Matrix:
    """SVG transform list as one matrix."""
    m = IDENTITY
    if not text:
        return m
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", text):
        v = [float(x) for x in _TOKEN.findall(args) if not x.isalpha()]
        if name == "matrix" and len(v) == 6:
            t = tuple(v)
        elif name == "translate" and v:
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale" and v:
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate" and v:
            r = math.radians(v[0])
            t = (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0)
            if len(v) == 3:
                t = _mul(_mul((1, 0, 0, 1, v[1], v[2]), t), (1, 0, 0, 1, -v[1], -v[2]))
        elif name == "skewX" and v:
            t = (1, 0, math.tan(math.radians(v[0])), 1, 0, 0)
        elif name == "skewY" and v:
            t = (1, math.tan(math.radians(v[0])), 0, 1, 0, 0)
        else:
            continue
        m = _mul(m, t)
    return m


def _arc_points(x0, y0, rx, ry, phi, large, sweep, x, y, steps=16):
    """Points along an SVG arc (endpoint parameterisation)."""
    if rx == 0 or ry == 0 or (x0 == x and y0 == y):
        return [(x, y)]
    rx, ry = abs(rx), abs(ry)
    p = math.radians(phi)
    cp, sp = math.cos(p), math.sin(p)
    dx, dy = (x0 - x) / 2, (y0 - y) / 2
    x1, y1 = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = (x1 * x1) / (rx * rx) + (y1 * y1) / (ry * ry)
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    den = rx * rx * y1 * y1 + ry * ry * x1 * x1
    co = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        co = -co
    cx1, cy1 = co * rx * y1 / ry, -co * ry * x1 / rx
    cx, cy = cp * cx1 - sp * cy1 + (x0 + x) / 2, sp * cx1 + cp * cy1 + (y0 + y) / 2

    def angle(ux, uy, vx, vy):
        return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)

    t1 = angle(1, 0, (x1 - cx1) / rx, (y1 - cy1) / ry)
    dt = angle((x1 - cx1) / rx, (y1 - cy1) / ry, (-x1 - cx1) / rx, (-y1 - cy1) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    pts = []
    for i in range(1, steps + 1):
        t = t1 + dt * i / steps
        ex, ey = rx * math.cos(t), ry * math.sin(t)
        pts.append((cp * ex - sp * ey + cx, sp * ex + cp * ey + cy))
    return pts


def _q2c(p0, q, p1):
    """Quadratic control point as the two cubic ones."""
    return ((p0[0] + 2 * (q[0] - p0[0]) / 3, p0[1] + 2 * (q[1] - p0[1]) / 3),
            (p1[0] + 2 * (q[0] - p1[0]) / 3, p1[1] + 2 * (q[1] - p1[1]) / 3))


def _cubic(p0, c1, c2, p1, steps=16):
    """Points along a cubic Bézier curve (without its start point)."""
    out = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1 - t
        a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
        out.append((a * p0[0] + b * c1[0] + c * c2[0] + d * p1[0],
                    a * p0[1] + b * c1[1] + c * c2[1] + d * p1[1]))
    return out


def path_points(d: str) -> list[tuple[float, float]]:
    """Points along a path (curves and arcs sampled), in path coordinates."""
    tokens = _TOKEN.findall(d or "")
    pts: list[tuple[float, float]] = []
    i = 0
    cmd = None
    x = y = sx = sy = 0.0
    last_cmd = ""
    last_c = last_q = (0.0, 0.0)

    def num():
        nonlocal i
        v = float(tokens[i])
        i += 1
        return v

    def flag():
        # arc flags may be written without separators, e.g. "011"
        nonlocal i
        t = tokens[i]
        if len(t) > 1 and t[0] in "01" and "." not in t[:2]:
            tokens[i] = t[1:]
            return int(t[0])
        i += 1
        return int(float(t))

    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                x, y = sx, sy
                last_cmd = "Z"
                continue
        if cmd is None:
            break
        up = cmd.upper()
        rel = cmd.islower()
        try:
            if up == "M":
                nx, ny = num(), num()
                x, y = (x + nx, y + ny) if rel else (nx, ny)
                sx, sy = x, y
                pts.append((x, y))
                cmd = "l" if rel else "L"  # further pairs are line-tos
            elif up == "L":
                nx, ny = num(), num()
                x, y = (x + nx, y + ny) if rel else (nx, ny)
                pts.append((x, y))
            elif up == "H":
                v = num()
                x = x + v if rel else v
                pts.append((x, y))
            elif up == "V":
                v = num()
                y = y + v if rel else v
                pts.append((x, y))
            elif up in "CSQT":
                vals = [num() for _ in range(_ARGS[up])]
                abs_pts = [(x + vals[k], y + vals[k + 1]) if rel else (vals[k], vals[k + 1])
                           for k in range(0, len(vals), 2)]
                if up == "C":
                    c1, c2, end = abs_pts
                elif up == "S":
                    c1 = (2 * x - last_c[0], 2 * y - last_c[1]) if last_cmd in ("C", "S") else (x, y)
                    c2, end = abs_pts
                elif up == "Q":
                    q, end = abs_pts
                    c1, c2 = _q2c((x, y), q, end)
                    last_q = q
                else:  # T
                    q = (2 * x - last_q[0], 2 * y - last_q[1]) if last_cmd in ("Q", "T") else (x, y)
                    end = abs_pts[0]
                    c1, c2 = _q2c((x, y), q, end)
                    last_q = q
                pts.extend(_cubic((x, y), c1, c2, end))
                last_c = c2
                x, y = end
            elif up == "A":
                rx, ry, phi = num(), num(), num()
                large, sweep = flag(), flag()
                nx, ny = num(), num()
                ex, ey = (x + nx, y + ny) if rel else (nx, ny)
                pts.extend(_arc_points(x, y, rx, ry, phi, large, sweep, ex, ey))
                x, y = ex, ey
            else:
                i += 1
        except (IndexError, ValueError):
            break
        last_cmd = up
    return pts


def ink_box(group: ET.Element) -> tuple[float, float, float, float] | None:
    """(x, y, w, h) around all drawn paths of a normalised SVG group, in the
    group's coordinates; None if nothing is drawn."""
    xs: list[float] = []
    ys: list[float] = []

    def walk(el: ET.Element, m: Matrix):
        if el.tag in ("defs", "clipPath", "linearGradient", "radialGradient", "stop"):
            return
        m = _mul(m, parse_transform(el.get("transform")))
        if el.tag == "path" and el.get("fill", "black") != "none" or (
                el.tag == "path" and el.get("stroke", "none") != "none"):
            a, b, c, d, e, f = m
            for px, py in path_points(el.get("d", "")):
                xs.append(a * px + c * py + e)
                ys.append(b * px + d * py + f)
        for child in el:
            walk(child, m)

    walk(group, IDENTITY)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
