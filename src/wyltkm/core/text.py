"""Text blocks as glyph outlines (see docs/designs.md, "Text blocks").

Lines are laid out from glyph advances with kerning, so spacing is under our
control: one font size for all lines, set by the widest line; ``center`` or
``justify`` alignment; highlighted runs in another colour.
"""

from __future__ import annotations

from dataclasses import dataclass

import ziafont

from .errors import DataError


@dataclass(frozen=True)
class Run:
    text: str
    highlight: bool = False


def parse_markers(line: str, where: str = "text", error: type[Exception] = DataError,
                  hint: str = "") -> list[Run]:
    """Split text into runs; ``[...]`` is highlighted, ``[[``/``]]`` are
    literal brackets. Unbalanced brackets raise ``error`` (message plus
    ``hint``)."""
    runs: list[Run] = []
    buf = ""
    highlight = False
    i = 0
    while i < len(line):
        c = line[i]
        if c in "[]" and line[i:i + 2] == c * 2:
            buf += c
            i += 2
            continue
        if c == "[":
            if highlight:
                raise error(f"{where}: nested '[' in {line!r}{hint}")
            if buf:
                runs.append(Run(buf, False))
            buf, highlight = "", True
        elif c == "]":
            if not highlight:
                raise error(f"{where}: ']' without '[' in {line!r}{hint}")
            if buf:
                runs.append(Run(buf, True))
            buf, highlight = "", False
        else:
            buf += c
        i += 1
    if highlight:
        raise error(f"{where}: '[' without ']' in {line!r}{hint}")
    if buf:
        runs.append(Run(buf, False))
    return runs


@dataclass
class _Glyph:
    glyph: object
    highlight: bool
    x: float  # pen position in font units
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    inked: bool


def _layout_line(font: ziafont.Font, runs: list[Run]) -> list[_Glyph]:
    chars = [(c, r.highlight) for r in runs for c in r.text]
    glyphs = [font.glyph(c) for c, _ in chars]
    out = []
    x = 0.0
    for i, g in enumerate(glyphs):
        nxt = glyphs[i + 1].index if i + 1 < len(glyphs) else None
        b = g.bbox
        inked = bool(g.operators)
        out.append(_Glyph(g, chars[i][1], x, b.xmin, b.xmax, b.ymin, b.ymax, inked))
        x += font.advance(g.index, nxt)
    return out


@dataclass(frozen=True)
class TextBlock:
    """Laid out text block: path data per colour role, in block units."""

    width: float
    height: float
    normal: str
    """Path data of normal text."""
    highlight: str
    """Path data of highlighted text."""


def cap_height(font: ziafont.Font) -> float:
    """Height of a capital letter in font units."""
    g = font.glyph("H")
    return g.bbox.ymax if g.operators else font.info.layout.ascent


def _inks(laid: list[list[_Glyph]]):
    inks = []
    for glyphs in laid:
        inked = [g for g in glyphs if g.inked]
        if inked:
            left = min(g.x + g.xmin for g in inked)
            right = max(g.x + g.xmax for g in inked)
            top = max(g.ymax for g in inked)
            bottom = min(g.ymin for g in inked)
            inks.append((left, right, top, bottom))
        else:
            inks.append(None)
    return inks


def ink_width(font: ziafont.Font, text: str) -> float:
    """Width of the ink of ``text`` in one line, in font units."""
    ink = _inks([_layout_line(font, [Run(text)])])[0]
    return ink[1] - ink[0] if ink else 0.0


def block(font: ziafont.Font, lines: list[list[Run]], width: float, align: str = "center",
          line_gap: float = 2.0) -> TextBlock | None:
    """Lay out ``lines`` to fill ``width``. Returns None if there is no ink.

    ``line_gap`` is the space between the ink of one line and the ink of the
    next, in the units of ``width``; an empty line takes the height of a
    capital letter plus one gap."""
    laid = [_layout_line(font, runs) for runs in lines]
    inks = _inks(laid)
    widest = max((ink[1] - ink[0] for ink in inks if ink), default=0)
    if widest <= 0:
        return None
    return _place(font, laid, inks, width / widest, width, align, line_gap)


def block_at(font: ziafont.Font, lines: list[list[Run]], scale: float,
             line_gap: float = 1.0) -> TextBlock | None:
    """Lay out ``lines`` left-aligned at a fixed ``scale`` (output units per
    font unit). The block is as wide as its widest line."""
    laid = [_layout_line(font, runs) for runs in lines]
    inks = _inks(laid)
    widest = max((ink[1] - ink[0] for ink in inks if ink), default=0)
    if widest <= 0:
        return None
    return _place(font, laid, inks, scale, widest * scale, "left", line_gap)


def _place(font, laid, inks, scale: float, width: float, align: str,
           line_gap: float) -> TextBlock:
    empty_line = cap_height(font) * scale + line_gap
    y = 0.0  # top of the ink of the next line
    last_bottom = 0.0
    parts = {False: [], True: []}
    started = False
    for glyphs, ink in zip(laid, inks):
        if ink is None:
            if started:
                y += empty_line
            continue
        started = True
        left, right, top, bottom = ink
        baseline = y + top * scale
        natural = (right - left) * scale
        inked_idx = [i for i, g in enumerate(glyphs) if g.inked]
        lo, hi = inked_idx[0], inked_idx[-1]
        for i, g in enumerate(glyphs):
            if not g.inked:
                continue
            x = (g.x - left) * scale
            if align == "justify" and hi > lo:
                x += (width - natural) * (i - lo) / (hi - lo)
            elif align == "center":
                x += (width - natural) / 2
            d = "".join(op.path(x, baseline, scale) for op in g.glyph.operators)
            parts[g.highlight].append(_close(d))
        last_bottom = baseline - bottom * scale
        y = last_bottom + line_gap
    return TextBlock(width=width, height=last_bottom, normal="".join(parts[False]),
                     highlight="".join(parts[True]))


def _close(d: str) -> str:
    """Close every subpath, as ziafont does for its own output."""
    d = d.strip()
    pieces = d.split("M ")
    return "".join(f"M {p.strip()} Z " for p in pieces if p.strip())
