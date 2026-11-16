"""QR code matrix and its paths, in module units."""

from __future__ import annotations

import math
from dataclasses import dataclass

import qrcode

from . import geometry


@dataclass(frozen=True)
class QrShapes:
    module_shape: str = "square"
    module_radius: float = 0.3
    finder_ring_shape: str = "square"
    finder_ring_radius: float = 1.0
    finder_centre_shape: str = "square"
    finder_centre_radius: float = 1.0


def matrix(content: str) -> list[list[bool]]:
    """Module matrix (rows of booleans), without quiet zone, level H."""
    qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_H, border=0)
    qr.add_data(content)
    qr.make(fit=True)
    return [list(row) for row in qr.get_matrix()]


def hole_size(n: int) -> int:
    """Side of the empty centre square for an icon, in modules.

    The formula of 0.2.2: about 30 % of the side of the code without the
    finder patterns (2 × 64 modules), which is what level H can lose. Made
    odd, so it is centred (``n`` is always odd).
    """
    size = math.floor(math.sqrt(n * n - 64 * 2) * 0.3)
    if size % 2 == 0:
        size -= 1
    return max(size, 0)


def _in_finder(n: int, row: int, col: int) -> bool:
    return (row < 7 and col < 7) or (row < 7 and col >= n - 7) or (row >= n - 7 and col < 7)


def _in_hole(n: int, hole: int, row: int, col: int) -> bool:
    if hole <= 0:
        return False
    centre = (n - 1) / 2
    return abs(row - centre) < hole / 2 and abs(col - centre) < hole / 2


def finder_origins(n: int) -> list[tuple[int, int]]:
    """Top left corners (x, y) of the three finder patterns."""
    return [(0, 0), (n - 7, 0), (0, n - 7)]


@dataclass(frozen=True)
class QrPaths:
    size: int
    """Modules per side."""
    hole: int
    """Side of the empty centre square (0: none)."""
    modules: str
    """Path data of all data modules."""
    rings: str
    """Path data of the three finder rings (draw with evenodd fill)."""
    centres: str
    """Path data of the three finder centres."""


def paths(content: str, shapes: QrShapes, with_hole: bool) -> QrPaths:
    """Path data of a QR code at origin 0,0, one unit per module."""
    m = matrix(content)
    n = len(m)
    hole = hole_size(n) if with_hole else 0
    parts = []
    for row in range(n):
        for col in range(n):
            if m[row][col] and not _in_finder(n, row, col) and not _in_hole(n, hole, row, col):
                parts.append(geometry.shape(shapes.module_shape, col, row, 1, shapes.module_radius))
    rings = []
    centres = []
    for x, y in finder_origins(n):
        if shapes.finder_ring_shape == "circle":
            rings.append(geometry.circle(x + 3.5, y + 3.5, 3.5))
            rings.append(geometry.circle(x + 3.5, y + 3.5, 2.5))
        else:
            r = shapes.finder_ring_radius if shapes.finder_ring_shape == "rounded" else 0
            rings.append(geometry.rect(x, y, 7, 7, r))
            rings.append(geometry.rect(x + 1, y + 1, 5, 5, max(r - 1, 0)))
        centres.append(geometry.shape(shapes.finder_centre_shape, x + 2, y + 2, 3,
                                      shapes.finder_centre_radius))
    return QrPaths(size=n, hole=hole, modules="".join(parts), rings="".join(rings),
                   centres="".join(centres))
