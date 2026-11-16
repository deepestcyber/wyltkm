"""Parsing, sanitising and normalising of SVG files (icons, bottom graphics).

See docs/icons.md, "Normalising". The result is a group of shapes as paths,
with styles resolved into attributes, optionally recoloured.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import defusedxml.ElementTree as SafeET
from defusedxml import DefusedXmlException

from . import geometry
from .bounds import ink_box
from .errors import DataError, InvalidRequest

SVG_NS = "http://www.w3.org/2000/svg"
_NS = "{" + SVG_NS + "}"

CONTAINERS = {"g", "switch", "defs", "clipPath", "linearGradient", "radialGradient"}
SHAPES = {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon"}
KEEP = CONTAINERS | SHAPES | {"stop"}

PAINT_ATTRS = {
    "fill", "fill-rule", "fill-opacity", "opacity", "stroke", "stroke-width",
    "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-opacity",
    "stroke-dasharray", "stroke-dashoffset", "clip-path", "clip-rule", "stop-color",
    "stop-opacity", "display", "visibility",
}
GEOMETRY_ATTRS = {
    "d", "transform", "id", "x1", "y1", "x2", "y2", "cx", "cy", "r", "fx", "fy",
    "gradientUnits", "gradientTransform", "spreadMethod", "offset", "clipPathUnits",
}
INHERITED = {"fill", "fill-rule", "fill-opacity", "stroke", "stroke-width", "clip-rule",
             "visibility"}


@dataclass
class Normalised:
    """A normalised SVG: a group element and its coordinate box."""

    group: ET.Element
    viewbox: tuple[float, float, float, float]
    warnings: list[str] = field(default_factory=list)
    ink: tuple[float, float, float, float] | None = None
    """Box around what is actually drawn; may reach outside the viewBox."""

    @property
    def box(self) -> tuple[float, float, float, float]:
        """The viewBox, grown to contain everything drawn: what placing and
        previews use, so nothing sticks out (Font Awesome 7 draws outside
        its viewBox for some icons)."""
        vx, vy, vw, vh = self.viewbox
        if self.ink is None:
            return self.viewbox
        ix, iy, iw, ih = self.ink
        x0, y0 = min(vx, ix), min(vy, iy)
        x1, y1 = max(vx + vw, ix + iw), max(vy + vh, iy + ih)
        return (x0, y0, x1 - x0, y1 - y0)

    @property
    def aspect(self) -> float:
        bx, by, bw, bh = self.box
        return bh / bw


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if tag.startswith("{") else tag


def _floats(text: str) -> list[float]:
    return [float(v) for v in re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", text or "")]


def _length(value: str | None, default: float = 0.0) -> float:
    if not value:
        return default
    nums = _floats(value)
    return nums[0] if nums else default


def _parse_css(text: str) -> list[tuple[str, dict[str, str]]]:
    """Very small CSS reader: ``selector, selector { prop: value; }``."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    rules = []
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", text):
        decls = _parse_style(body)
        for sel in selectors.split(","):
            sel = sel.strip()
            if sel:
                rules.append((sel, decls))
    return rules


def _parse_style(text: str) -> dict[str, str]:
    decls = {}
    for item in (text or "").split(";"):
        if ":" in item:
            k, v = item.split(":", 1)
            decls[k.strip()] = v.strip()
    return decls


def _matches(sel: str, tag: str, classes: set[str]) -> bool:
    if sel == "*":
        return True
    if sel.startswith("."):
        return sel[1:] in classes
    if "." in sel:
        t, c = sel.split(".", 1)
        return t == tag and c in classes
    return sel == tag


def _shape_to_path(tag: str, el: ET.Element) -> str | None:
    g = el.get
    if tag == "path":
        return g("d")
    if tag == "rect":
        x, y = _length(g("x")), _length(g("y"))
        w, h = _length(g("width")), _length(g("height"))
        if w <= 0 or h <= 0:
            return None
        rx, ry = g("rx"), g("ry")
        r = _length(rx if rx is not None else ry)
        return geometry.rect(x, y, w, h, r)
    if tag == "circle":
        r = _length(g("r"))
        return geometry.circle(_length(g("cx")), _length(g("cy")), r) if r > 0 else None
    if tag == "ellipse":
        rx, ry = _length(g("rx")), _length(g("ry"))
        if rx <= 0 or ry <= 0:
            return None
        return geometry.ellipse(_length(g("cx")), _length(g("cy")), rx, ry)
    if tag == "line":
        return (f"M{geometry.num(_length(g('x1')))} {geometry.num(_length(g('y1')))}"
                f"L{geometry.num(_length(g('x2')))} {geometry.num(_length(g('y2')))}")
    if tag in ("polyline", "polygon"):
        pts = _floats(g("points"))
        if len(pts) < 4:
            return None
        coords = [f"{geometry.num(pts[i])} {geometry.num(pts[i + 1])}" for i in range(0, len(pts) - 1, 2)]
        d = "M" + "L".join(coords)
        return d + "Z" if tag == "polygon" else d
    return None


class _Normaliser:
    def __init__(self, id_prefix: str, max_elements: int, max_depth: int, where: str,
                 error: type[Exception]):
        self.id_prefix = id_prefix
        self.max_elements = max_elements
        self.max_depth = max_depth
        self.where = where
        self.error = error
        self.count = 0
        self.rules: list[tuple[str, dict[str, str]]] = []
        self.stroked = False
        self.clipped = False
        self.gradient = False

    def collect_styles(self, root: ET.Element):
        for el in root.iter():
            if _local(el.tag) == "style":
                self.rules.extend(_parse_css("".join(el.itertext())))

    def styles_of(self, tag: str, el: ET.Element) -> dict[str, str]:
        """Presentation attributes, then CSS rules, then the style attribute."""
        props = {k: v for k, v in el.attrib.items() if k in PAINT_ATTRS}
        classes = set((el.get("class") or "").split())
        for sel, decls in self.rules:
            if _matches(sel, tag, classes):
                props.update({k: v for k, v in decls.items() if k in PAINT_ATTRS})
        props.update({k: v for k, v in _parse_style(el.get("style")).items() if k in PAINT_ATTRS})
        return props

    def convert(self, el: ET.Element, depth: int) -> ET.Element | None:
        tag = _local(el.tag)
        if tag not in KEEP and tag != "svg":
            return None
        self.count += 1
        if self.count > self.max_elements:
            raise self.error(f"{self.where}: more than {self.max_elements} elements")
        if depth > self.max_depth:
            raise self.error(f"{self.where}: nested deeper than {self.max_depth}")
        props = self.styles_of(tag, el)
        if props.get("display") == "none":
            return None
        out_tag = "g" if tag in ("svg", "switch") else ("path" if tag in SHAPES else tag)
        out = ET.Element(out_tag)
        if tag in SHAPES:
            d = _shape_to_path(tag, el)
            if not d:
                return None
            out.set("d", d)
        for k in sorted(GEOMETRY_ATTRS - {"d"}):
            v = el.get(k)
            if v is None or (tag == "svg" and k != "id"):
                continue
            if k in ("x1", "y1", "x2", "y2", "cx", "cy", "r", "fx", "fy") and tag not in (
                    "linearGradient", "radialGradient"):
                continue
            if k == "id":
                v = self.id_prefix + v
            out.set(k, v)
        for k, v in sorted(props.items()):
            out.set(k, self.prefix_refs(v))
        if "clip-path" in props:
            self.clipped = True
        if tag in ("linearGradient", "radialGradient"):
            self.gradient = True
        for child in el:
            c = self.convert(child, depth + 1)
            if c is not None:
                out.append(c)
                if tag == "switch":
                    break  # a switch draws only its first usable child
        if tag in ("defs", "g", "clipPath") and len(out) == 0:
            return None  # nothing to draw or reference
        return out

    def prefix_refs(self, value: str) -> str:
        return re.sub(r"url\(\s*#([^)\s]+)\s*\)", lambda m: f"url(#{self.id_prefix}{m.group(1)})", value)


def _viewbox(root: ET.Element, where: str, error) -> tuple[float, float, float, float]:
    vb = _floats(root.get("viewBox") or "")
    if len(vb) == 4 and vb[2] > 0 and vb[3] > 0:
        return tuple(vb)
    w, h = _length(root.get("width")), _length(root.get("height"))
    if w > 0 and h > 0:
        return (0.0, 0.0, w, h)
    raise error(f"{where}: SVG has neither viewBox nor width and height")


def _effective(el: ET.Element, parents: list[ET.Element], key: str, default: str) -> str:
    for node in [el, *reversed(parents)]:
        if key in node.attrib:
            return node.get(key)
    return default


def _paint(el: ET.Element, parents: list[ET.Element], colour: str | None, norm: _Normaliser):
    """Resolve inherited fill and stroke onto shapes; recolour if asked;
    note strokes. Works in place."""
    stack: list[tuple[ET.Element, list[ET.Element]]] = [(el, [])]
    while stack:
        node, chain = stack.pop()
        if node.tag in ("clipPath", "linearGradient", "radialGradient", "defs"):
            continue
        if node.tag == "path":
            fill = _effective(node, chain, "fill", "black")
            stroke = _effective(node, chain, "stroke", "none")
            width = _length(_effective(node, chain, "stroke-width", "1"), 1.0)
            has_stroke = stroke != "none" and width > 0
            if has_stroke:
                norm.stroked = True
            if colour is not None:
                if fill != "none":
                    node.set("fill", colour)
                if has_stroke:
                    node.set("stroke", colour)
            else:
                node.set("fill", fill)
        for child in list(node):
            stack.append((child, [*chain, node]))
    if colour is not None:
        for node in el.iter():
            if node.tag == "g":
                for k in ("fill", "stroke"):
                    node.attrib.pop(k, None)


def normalise(data: bytes, *, recolour: str | None = None, id_prefix: str = "i-",
              max_elements: int = 20000, max_depth: int = 50, where: str = "SVG",
              untrusted: bool = False) -> Normalised:
    """Parse and normalise SVG ``data``.

    ``recolour``: fill all visible shapes with this colour. ``untrusted``:
    errors are ``InvalidRequest`` (for uploads) instead of ``DataError``.
    """
    error = InvalidRequest if untrusted else DataError
    try:
        root = SafeET.fromstring(data, forbid_dtd=True, forbid_entities=True,
                                 forbid_external=True)
    except (ET.ParseError, DefusedXmlException, ValueError) as e:
        raise error(f"{where}: not a valid SVG file ({e})") from e
    if _local(root.tag) != "svg":
        raise error(f"{where}: root element is not <svg>")
    vb = _viewbox(root, where, error)
    norm = _Normaliser(id_prefix, max_elements, max_depth, where, error)
    norm.collect_styles(root)
    group = norm.convert(root, 0)
    if group is None or len(group) == 0:
        raise error(f"{where}: SVG contains no shapes")
    _paint(group, [], recolour, norm)
    warnings = []
    reasons = [r for r, on in (("strokes", norm.stroked), ("clip paths", norm.clipped),
                               ("gradients", norm.gradient)) if on]
    if reasons:
        warnings.append(f"{where} is not laser-friendly: uses {', '.join(reasons)}")
    return Normalised(group=group, viewbox=vb, warnings=warnings, ink=ink_box(group))


def place(n: Normalised, x: float, y: float, w: float, h: float) -> ET.Element:
    """Wrap ``n`` in a group that fits it into the box, keeping its aspect
    ratio, centred."""
    vx, vy, vw, vh = n.box
    s = min(w / vw, h / vh)
    ox = x + (w - vw * s) / 2 - vx * s
    oy = y + (h - vh * s) / 2 - vy * s
    g = ET.Element("g", transform=f"translate({geometry.num(ox)} {geometry.num(oy)}) "
                                  f"scale({s:.6g})")
    g.append(n.group)
    return g
