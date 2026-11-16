"""Readable side text: the content of the QR code along the right side
(see docs/rendering.md, "Readable side text")."""

from __future__ import annotations

from dataclasses import dataclass

import ziafont

from . import text as textmod
from .text import Run

BREAK_AFTER = set("/?&=.-_# ")
COLUMN_GAP = 1.0
"""Space between columns, in modules."""


def _pieces(line: str) -> list[str]:
    """Split a line after break characters; each piece keeps its break
    character at the end."""
    pieces, cur = [], ""
    for c in line:
        cur += c
        if c in BREAK_AFTER:
            pieces.append(cur)
            cur = ""
    if cur:
        pieces.append(cur)
    return pieces


class _Measure:
    """Approximate widths from glyph advances (without kerning), fast enough
    to try many splits; the final size uses exact ink widths."""

    def __init__(self, font: ziafont.Font):
        self.font = font
        self._adv: dict[str, float] = {}

    def __call__(self, s: str) -> float:
        s = s.rstrip()
        total = 0.0
        for c in s:
            if c not in self._adv:
                g = self.font.glyph(c)
                self._adv[c] = float(self.font.advance(g.index, None))
            total += self._adv[c]
        return total


def _pack(lines: list[list[str]], limit: float, measure: _Measure) -> list[str]:
    """Greedy: fill each column up to ``limit``; content line breaks always
    start a new column; a piece longer than ``limit`` is broken anywhere."""
    columns: list[str] = []
    for pieces in lines:
        cur = ""
        for piece in pieces:
            if measure(cur + piece) <= limit:
                cur += piece
                continue
            if cur.strip():
                columns.append(cur)
            cur = ""
            if measure(piece) <= limit:
                cur = piece
                continue
            for c in piece:  # hard break
                if cur and measure(cur + c) > limit:
                    columns.append(cur)
                    cur = ""
                cur += c
        if cur.strip():
            columns.append(cur)
    return columns


def _smallest_limit(lines, columns: int, lo: float, hi: float, measure) -> float:
    """Smallest limit (within 0.1 %) that packs into at most ``columns``."""
    for _ in range(40):
        mid = (lo + hi) / 2
        if len(_pack(lines, mid, measure)) <= columns:
            hi = mid
        else:
            lo = mid
        if hi - lo <= hi * 0.001:
            break
    return hi


@dataclass(frozen=True)
class SideLayout:
    columns: list[str]
    scale: float
    """Modules per font unit."""
    warning: str | None = None


def layout(font: ziafont.Font, content: str, length: float, min_size: float,
           max_size: float, max_columns: int) -> SideLayout | None:
    """Split ``content`` into columns of at most ``length`` modules and pick
    the font size. ``min_size``/``max_size`` are cap heights in modules."""
    lines = [_pieces(line) for line in content.replace("\r\n", "\n").split("\n")]
    measure = _Measure(font)
    cap = textmod.cap_height(font)
    if cap <= 0 or not any(measure("".join(p)) for p in lines):
        return None
    full = max(measure("".join(p)) for p in lines)
    widest_char = max(measure(c) for p in lines for c in "".join(p))
    allowed = length * cap / min_size  # longest column at the minimum size
    warning = None
    n = len(_pack(lines, allowed, measure))
    if n > max_columns:
        n = max_columns
        warning = (f"side text needs more than {max_columns} columns at its minimum size; "
                   "it is drawn smaller")
    limit = _smallest_limit(lines, n, widest_char, max(full, allowed), measure)
    columns = [c.rstrip() for c in _pack(lines, limit, measure)]
    exact = max(textmod.ink_width(font, c) for c in columns)
    scale = min(length / exact, max_size / cap)
    return SideLayout(columns, scale, warning)


def block(font: ziafont.Font, content: str, length: float, min_size: float, max_size: float,
          max_columns: int, warnings: list[str]) -> textmod.TextBlock | None:
    """The side text as an unrotated block: lines are the columns, the
    block's width runs along the image height."""
    lay = layout(font, content, length, min_size, max_size, max_columns)
    if lay is None:
        return None
    if lay.warning:
        warnings.append(lay.warning)
    return textmod.block_at(font, [[Run(c)] for c in lay.columns], lay.scale, COLUMN_GAP)
