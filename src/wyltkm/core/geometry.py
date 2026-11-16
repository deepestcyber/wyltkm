"""Path data for basic shapes, with deterministic number formatting.

All functions return SVG path data strings. Coordinates are in whatever unit
the caller uses (the renderer uses QR modules).
"""

from __future__ import annotations


def num(value: float) -> str:
    """Format a number with at most 3 decimals, without trailing zeros."""
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def rect(x: float, y: float, w: float, h: float, r: float = 0.0) -> str:
    """Rectangle, optionally with rounded corners of radius ``r``."""
    r = max(0.0, min(r, w / 2, h / 2))
    if r == 0:
        return f"M{num(x)} {num(y)}H{num(x + w)}V{num(y + h)}H{num(x)}Z"
    a = f"A{num(r)} {num(r)} 0 0 1 "
    return (
        f"M{num(x + r)} {num(y)}H{num(x + w - r)}{a}{num(x + w)} {num(y + r)}"
        f"V{num(y + h - r)}{a}{num(x + w - r)} {num(y + h)}"
        f"H{num(x + r)}{a}{num(x)} {num(y + h - r)}"
        f"V{num(y + r)}{a}{num(x + r)} {num(y)}Z"
    )


def circle(cx: float, cy: float, r: float) -> str:
    """Circle as two arcs."""
    a = f"A{num(r)} {num(r)} 0 1 0 "
    return f"M{num(cx - r)} {num(cy)}{a}{num(cx + r)} {num(cy)}{a}{num(cx - r)} {num(cy)}Z"


def ellipse(cx: float, cy: float, rx: float, ry: float) -> str:
    a = f"A{num(rx)} {num(ry)} 0 1 0 "
    return f"M{num(cx - rx)} {num(cy)}{a}{num(cx + rx)} {num(cy)}{a}{num(cx - rx)} {num(cy)}Z"


def shape(kind: str, x: float, y: float, size: float, radius: float) -> str:
    """A square area at ``x, y`` of side ``size``, drawn as ``square``,
    ``rounded`` (corner ``radius``), ``circle`` or ``dot`` (both a circle)."""
    if kind in ("circle", "dot"):
        half = size / 2
        return circle(x + half, y + half, half)
    if kind == "rounded":
        return rect(x, y, size, size, radius)
    return rect(x, y, size, size)
