"""Designs: loading, inheritance, colour schemes (see docs/designs.md)."""

from __future__ import annotations

import copy
import logging
import re
import tomllib
from dataclasses import dataclass, replace
from importlib import resources
from pathlib import Path

from . import licences
from .errors import DataError, InvalidRequest, UnknownDesign
from .licences import Licence
from .qr import QrShapes
from .request import NO_ICON, valid_icon_name, valid_name
from .text import Run, parse_markers

log = logging.getLogger(__name__)

BUILTIN_DIR = Path(str(resources.files("wyltkm.core") / "data" / "designs"))

COLOUR_FALLBACKS = {
    # colour: what it falls back to, in order of resolution
    "finder_ring": "modules",
    "finder_centre": "finder_ring",
    "icon": "modules",
    "top": "modules",
    "bottom": "top",
    "highlight": "bottom",
    "side": "top",
}
COLOURS = ("background", "modules", *COLOUR_FALLBACKS)
REQUIRED_COLOURS = ("background", "modules")
COLOUR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

TOP_KEYS = {"name", "title", "description", "order", "extends", "default_scheme", "colours", "schemes",
            "qr", "top", "bottom", "side", "defaults", "licence"}
TABLE_KEYS = {
    "qr": {"module_shape", "module_radius", "finder_ring_shape", "finder_ring_radius",
           "finder_centre_shape", "finder_centre_radius"},
    "top": {"fonts", "align", "gap", "line_gap"},
    "bottom": {"type", "lines", "fonts", "align", "gap", "line_gap", "svg", "recolour"},
    "side": {"fonts", "direction", "gap", "min_size", "max_size", "max_columns"},
    "defaults": {"icon", "border", "background"},
}
SCHEME_FONT_KEYS = {"top", "bottom", "side"}
"""Fonts a scheme may change, in its ``fonts`` table."""
MODULE_SHAPES = {"square", "rounded", "dot"}
FINDER_SHAPES = {"square", "rounded", "circle"}
ALIGNS = {"center", "justify"}


@dataclass(frozen=True)
class TextStyle:
    fonts: tuple[str, ...] = ()
    align: str = "justify"
    gap: float = 2.0
    """Space between this text (or graphic) and the QR code, in modules."""
    line_gap: float = 2.0
    """Space between the lines, in modules."""


@dataclass(frozen=True)
class Bottom:
    type: str = "none"
    lines: tuple[tuple[Run, ...], ...] = ()
    style: TextStyle = TextStyle(align="justify")
    svg: Path | None = None
    recolour: bool = False


@dataclass(frozen=True)
class Side:
    fonts: tuple[str, ...] = ("Hack-Regular.ttf",)
    direction: str = "up"
    min_size: float = 1.5
    max_size: float = 3.0
    max_columns: int = 4
    gap: float = 2.0
    """Space between the main column and the side text, in modules."""


@dataclass(frozen=True)
class Defaults:
    icon: str = NO_ICON
    border: bool = False
    background: bool = True


@dataclass(frozen=True)
class Scheme:
    name: str
    title: str
    colours: dict[str, str]
    """Fully resolved colours (fallbacks applied)."""
    icon: str | None = None
    """Default icon of this scheme, instead of the design's."""
    top: "TextStyle | None" = None
    """Top text style with this scheme's fonts, if it sets them."""
    bottom: "TextStyle | None" = None
    """Bottom text style with this scheme's fonts, if it sets them."""
    side_fonts: tuple[str, ...] | None = None
    """Side text fonts of this scheme, if it sets them."""


@dataclass(frozen=True)
class Design:
    name: str
    title: str
    description: str
    order: float
    """Position in lists: lower first, then by name."""
    dirs: tuple[Path, ...]
    """Directory of the design, then those of its parents."""
    base_colours: dict[str, str]
    """Resolved colours for a design without schemes."""
    schemes: dict[str, Scheme]
    default_scheme: str | None
    qr: QrShapes
    top: TextStyle
    bottom: Bottom
    side: Side
    defaults: Defaults
    licence: Licence

    def colours(self, scheme: str | None = None) -> dict[str, str]:
        if not self.schemes:
            if scheme is not None:
                raise InvalidRequest(f"design {self.name} has no colour schemes")
            return self.base_colours
        name = scheme or self.default_scheme
        if name not in self.schemes:
            raise InvalidRequest(
                f"design {self.name} has no scheme {name!r}; "
                f"schemes: {', '.join(self.schemes)}")
        return self.schemes[name].colours

    def _scheme(self, scheme: str | None) -> "Scheme | None":
        if not self.schemes:
            return None
        return self.schemes.get(scheme or self.default_scheme)

    def top_style(self, scheme: str | None = None) -> TextStyle:
        """Top text style for a scheme (the scheme's if it sets one)."""
        s = self._scheme(scheme)
        return s.top if s is not None and s.top is not None else self.top

    def bottom_style(self, scheme: str | None = None) -> TextStyle:
        """Bottom text style for a scheme (the scheme's if it sets one)."""
        s = self._scheme(scheme)
        return s.bottom if s is not None and s.bottom is not None else self.bottom.style

    def side_fonts(self, scheme: str | None = None) -> tuple[str, ...]:
        """Default side text fonts for a scheme."""
        s = self._scheme(scheme)
        return s.side_fonts if s is not None and s.side_fonts is not None else self.side.fonts

    def default_icon(self, scheme: str | None = None) -> str:
        """The icon used when the request names none: the scheme's, if it
        sets one, else the design's."""
        if self.schemes:
            s = self.schemes.get(scheme or self.default_scheme)
            if s is not None and s.icon is not None:
                return s.icon
        return self.defaults.icon


def _luminance(colour: str) -> float:
    channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio of two ``#rrggbb`` colours (1 to 21)."""
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


MIN_CONTRAST = 3.0
"""Below this contrast against the background, ``wyltkm designs show`` warns;
QR codes then may not scan everywhere."""


def _merge(base: dict, over: dict) -> dict:
    """Merge tables key by key; nested tables recursively."""
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _resolve_colours(raw: dict, where: str) -> dict[str, str]:
    for k, v in raw.items():
        if k not in COLOURS:
            raise DataError(f"{where}: unknown colour {k!r}")
        if not isinstance(v, str) or not COLOUR_RE.match(v):
            raise DataError(f"{where}: colour {k} must be #rrggbb, not {v!r}")
    for k in REQUIRED_COLOURS:
        if k not in raw:
            raise DataError(f"{where}: colour {k} is required")
    out = {k: raw[k].lower() for k in REQUIRED_COLOURS}
    for k, fallback in COLOUR_FALLBACKS.items():
        out[k] = raw.get(k, out[fallback]).lower()
    return out


class DesignRegistry:
    """Designs by name, from design root directories (first wins)."""

    def __init__(self, roots: list[Path] | None = None):
        self.roots = list(roots) if roots is not None else [BUILTIN_DIR]
        self._dirs: dict[str, Path] = {}
        for root in self.roots:
            if not root.is_dir():
                continue
            for d in sorted(root.iterdir()):
                if (d / "design.toml").is_file():
                    if d.name in self._dirs:
                        log.info("design %s in %s overrides %s", d.name, root, self._dirs[d.name])
                        continue
                    self._dirs[d.name] = d
        self._cache: dict[str, Design] = {}

    def names(self) -> list[str]:
        return sorted(self._dirs)

    def all(self) -> list[Design]:
        return [self.get(n) for n in self.names()]

    def _raw(self, name: str, chain: tuple[str, ...] = ()) -> tuple[dict, list[Path]]:
        if name in chain:
            raise DataError(f"design {chain[0]}: inheritance cycle via {name}")
        d = self._dirs.get(name)
        if d is None:
            if chain:
                raise DataError(f"design {chain[-1]}: extends unknown design {name!r}")
            raise UnknownDesign(f"unknown design: {name}")
        path = d / "design.toml"
        try:
            raw = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as e:
            raise DataError(f"{path}: {e}") from e
        _check_keys(raw, path)
        if raw.get("name") != name:
            raise DataError(f"{path}: name must be {name!r}")
        parent = raw.get("extends") or ""
        if parent:
            praw, pdirs = self._raw(parent, (*chain, name))
            # name, title, description, licence belong to the design itself
            for k in ("name", "title", "description", "order", "extends", "licence"):
                praw.pop(k, None)
            return _merge(praw, raw), [d, *pdirs]
        return raw, [d]

    def get(self, name: str) -> Design:
        if name not in self._cache:
            if not valid_name(name):
                raise UnknownDesign(f"unknown design: {name}")
            raw, dirs = self._raw(name)
            self._cache[name] = _build(raw, dirs)
        return self._cache[name]


def _check_keys(raw: dict, path: Path):
    extra = set(raw) - TOP_KEYS
    if extra:
        raise DataError(f"{path}: unknown keys: {', '.join(sorted(extra))}")
    for table, keys in TABLE_KEYS.items():
        if table in raw:
            if not isinstance(raw[table], dict):
                raise DataError(f"{path}: {table} must be a table")
            extra = set(raw[table]) - keys
            if extra:
                raise DataError(f"{path}: unknown keys in [{table}]: {', '.join(sorted(extra))}")
    for sname, s in (raw.get("schemes") or {}).items():
        if not isinstance(s, dict):
            raise DataError(f"{path}: schemes.{sname} must be a table")
        if "fonts" in s:
            if not isinstance(s["fonts"], dict):
                raise DataError(f"{path}: schemes.{sname}.fonts must be a table")
            extra = set(s["fonts"]) - SCHEME_FONT_KEYS
            if extra:
                raise DataError(f"{path}: unknown keys in [schemes.{sname}.fonts]: "
                                f"{', '.join(sorted(extra))}")


def _str(v, where, default=None):
    if v is None:
        return default
    if not isinstance(v, str):
        raise DataError(f"{where} must be a string")
    return v


def _num(v, where, default, lo=0.0, hi=1000.0):
    if v is None:
        return default
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi:
        raise DataError(f"{where} must be a number from {lo} to {hi}")
    return float(v)


def _bool(v, where, default):
    if v is None:
        return default
    if not isinstance(v, bool):
        raise DataError(f"{where} must be true or false")
    return v


def _choice(v, where, choices, default):
    if v is None:
        return default
    if v not in choices:
        raise DataError(f"{where} must be one of {', '.join(sorted(choices))}")
    return v


def _fonts(v, where, default=()):
    if v is None:
        return tuple(default)
    if not isinstance(v, list) or not all(isinstance(f, str) and f for f in v):
        raise DataError(f"{where} must be a list of font file names")
    return tuple(v)


def _text_style(t: dict, where: str, align_default: str) -> TextStyle:
    return TextStyle(
        fonts=_fonts(t.get("fonts"), f"{where}.fonts"),
        align=_choice(t.get("align"), f"{where}.align", ALIGNS, align_default),
        gap=_num(t.get("gap"), f"{where}.gap", 2.0, 0, 20),
        line_gap=_num(t.get("line_gap"), f"{where}.line_gap",
                      _num(t.get("gap"), f"{where}.gap", 2.0, 0, 20), 0, 20),
    )


def _build(raw: dict, dirs: list[Path]) -> Design:
    name = raw["name"]
    where = f"design {name}"
    title = _str(raw.get("title"), f"{where}: title")
    if not title:
        raise DataError(f"{where}: title is required")

    colours_raw = raw.get("colours") or {}
    schemes_raw = raw.get("schemes") or {}
    schemes = {}
    scheme_fonts: dict[str, dict] = {}
    for sname, s in schemes_raw.items():
        if not valid_name(sname):
            raise DataError(f"{where}: invalid scheme name {sname!r}")
        s = dict(s)
        stitle = _str(s.pop("title", None), f"{where}: schemes.{sname}.title")
        if not stitle:
            raise DataError(f"{where}: schemes.{sname} needs a title")
        scheme_fonts[sname] = s.pop("fonts", None) or {}
        sicon = _str(s.pop("default_icon", None), f"{where}: schemes.{sname}.default_icon")
        if sicon is not None and sicon != NO_ICON and not valid_icon_name(sicon):
            raise DataError(f"{where}: schemes.{sname}.default_icon must be source:name or none")
        schemes[sname] = Scheme(sname, stitle,
                                _resolve_colours({**colours_raw, **s}, f"{where}, scheme {sname}"),
                                sicon)
    default_scheme = raw.get("default_scheme")
    if schemes:
        if default_scheme not in schemes:
            raise DataError(f"{where}: default_scheme must name one of its schemes")
        base = schemes[default_scheme].colours
    else:
        if default_scheme:
            raise DataError(f"{where}: default_scheme without schemes")
        base = _resolve_colours(colours_raw, where)

    q = raw.get("qr") or {}
    qr = QrShapes(
        module_shape=_choice(q.get("module_shape"), f"{where}: qr.module_shape", MODULE_SHAPES, "square"),
        module_radius=_num(q.get("module_radius"), f"{where}: qr.module_radius", 0.3, 0, 0.5),
        finder_ring_shape=_choice(q.get("finder_ring_shape"), f"{where}: qr.finder_ring_shape",
                                  FINDER_SHAPES, "square"),
        finder_ring_radius=_num(q.get("finder_ring_radius"), f"{where}: qr.finder_ring_radius",
                                1.0, 0, 3.5),
        finder_centre_shape=_choice(q.get("finder_centre_shape"), f"{where}: qr.finder_centre_shape",
                                    FINDER_SHAPES, "square"),
        finder_centre_radius=_num(q.get("finder_centre_radius"),
                                  f"{where}: qr.finder_centre_radius", 1.0, 0, 1.5),
    )

    top = _text_style(raw.get("top") or {}, f"{where}: top", "justify")

    b = raw.get("bottom") or {}
    btype = _choice(b.get("type"), f"{where}: bottom.type", {"text", "svg", "none"}, "none")
    bottom = Bottom(type=btype, style=_text_style(b, f"{where}: bottom", "justify"),
                    recolour=_bool(b.get("recolour"), f"{where}: bottom.recolour", False))
    if btype == "text":
        lines = b.get("lines")
        if not isinstance(lines, list) or not lines or not all(isinstance(x, str) for x in lines):
            raise DataError(f"{where}: bottom.lines must be a list of strings")
        parsed = tuple(tuple(parse_markers(x, f"{where}: bottom.lines")) for x in lines)
        bottom = Bottom(type=btype, lines=parsed, style=bottom.style)
    elif btype == "svg":
        file = _str(b.get("svg"), f"{where}: bottom.svg")
        if not file or "/" in file or file.startswith("."):
            raise DataError(f"{where}: bottom.svg must be a file name in the design directory")
        found = next((d / file for d in dirs if (d / file).is_file()), None)
        if found is None:
            raise DataError(f"{where}: bottom.svg {file} not found")
        bottom = Bottom(type=btype, style=bottom.style, svg=found, recolour=bottom.recolour)

    for sname, sf in scheme_fonts.items():
        swhere = f"{where}: schemes.{sname}.fonts"
        schemes[sname] = replace(
            schemes[sname],
            top=replace(top, fonts=_fonts(sf["top"], f"{swhere}.top")) if "top" in sf else None,
            bottom=replace(bottom.style, fonts=_fonts(sf["bottom"], f"{swhere}.bottom"))
            if "bottom" in sf else None,
            side_fonts=_fonts(sf["side"], f"{swhere}.side") if "side" in sf else None)

    s = raw.get("side") or {}
    side = Side(
        fonts=_fonts(s.get("fonts"), f"{where}: side.fonts", Side.fonts),
        direction=_choice(s.get("direction"), f"{where}: side.direction", {"up", "down"}, "up"),
        min_size=_num(s.get("min_size"), f"{where}: side.min_size", 1.5, 0.1, 100),
        max_size=_num(s.get("max_size"), f"{where}: side.max_size", 3.0, 0.1, 100),
        max_columns=int(_num(s.get("max_columns"), f"{where}: side.max_columns", 4, 1, 20)),
        gap=_num(s.get("gap"), f"{where}: side.gap", 2.0, 0, 20),
    )
    if side.max_size < side.min_size:
        raise DataError(f"{where}: side.max_size must not be smaller than side.min_size")

    df = raw.get("defaults") or {}
    icon = _str(df.get("icon"), f"{where}: defaults.icon", NO_ICON)
    if icon != NO_ICON and not valid_icon_name(icon):
        raise DataError(f"{where}: defaults.icon must be source:name or none")
    defaults = Defaults(icon=icon,
                        border=_bool(df.get("border"), f"{where}: defaults.border", False),
                        background=_bool(df.get("background"), f"{where}: defaults.background", True))

    part = f"Design {name}"
    licence = (licences.from_table(part, raw["licence"], where) if "licence" in raw
               else licences.unknown(part))

    return Design(name=name, title=title,
                  description=_str(raw.get("description"), f"{where}: description", ""),
                  order=_num(raw.get("order"), f"{where}: order", 100.0, -1000, 1000),
                  dirs=tuple(dirs), base_colours=base, schemes=schemes,
                  default_scheme=default_scheme if schemes else None, qr=qr, top=top,
                  bottom=bottom, side=side, defaults=defaults, licence=licence)
