"""Rendering: layout and SVG assembly, PNG (see docs/rendering.md)."""

from __future__ import annotations

import struct
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field

import cairosvg

from . import qr as qrmod
from . import side as sidemod
from . import svg as svgmod
from . import text as textmod
from .errors import InvalidRequest
from .geometry import num
from .licences import Licence
from .library import Library
from .request import NO_ICON, Request

BORDER = 4

UPLOAD_LICENCE = Licence(part="Icon (uploaded)", name="uploaded by the user")


@dataclass
class Result:
    svg: str
    width: int
    height: float
    warnings: list[str] = field(default_factory=list)
    licences: list[Licence] = field(default_factory=list)
    png: bytes | None = None
    modules: int = 0
    """Modules per side of the QR code."""

    @property
    def licence_notes(self) -> list[Licence]:
        """Licences the user should be told about (attribution, unclear)."""
        return [lic for lic in self.licences if lic.needs_note]


class _Parts:
    def __init__(self):
        self.warnings: list[str] = []
        self.licences: list[Licence] = []

    def licence(self, lic: Licence):
        if lic not in self.licences:
            self.licences.append(lic)


def _text_block(library: Library, design, style, lines, width, parts: _Parts):
    font = library.fonts.resolve(style.fonts, list(design.dirs), parts.warnings)
    blk = textmod.block(font.font, lines, width, style.align, style.line_gap)
    if blk is not None:
        parts.licence(font.licence)
    return blk


def _paths_group(blk: textmod.TextBlock, x: float, y: float, normal: str,
                 highlight: str) -> ET.Element:
    g = ET.Element("g", transform=f"translate({num(x)} {num(y)})")
    if blk.normal:
        ET.SubElement(g, "path", d=blk.normal, fill=normal)
    if blk.highlight:
        ET.SubElement(g, "path", d=blk.highlight, fill=highlight)
    return g


def _icon(library: Library, request: Request, design, colour: str, parts: _Parts):
    if request.icon_svg is not None:
        n = svgmod.normalise(request.icon_svg, recolour=None, id_prefix="icon-",
                             where="uploaded icon", untrusted=True,
                             max_elements=library.upload_max_elements,
                             max_depth=library.upload_max_depth)
        parts.licence(UPLOAD_LICENCE)
        parts.warnings.extend(n.warnings)
        return n
    name = request.icon if request.icon is not None else design.default_icon(request.scheme)
    if name == NO_ICON:
        return None
    src, n = library.icon(name, colour)
    parts.licence(src.licence)
    parts.warnings.extend(n.warnings)
    return n


def _metadata(licences: list[Licence]) -> ET.Element:
    md = ET.Element("metadata")
    rdf = ET.SubElement(md, "rdf:RDF", {
        "xmlns:rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "xmlns:cc": "http://creativecommons.org/ns#",
        "xmlns:dc": "http://purl.org/dc/elements/1.1/",
    })
    work = ET.SubElement(rdf, "cc:Work", {"rdf:about": ""})
    rights = ET.SubElement(work, "dc:rights")
    rights.text = licence_text(licences)
    for lic in licences:
        if lic.url:
            ET.SubElement(work, "cc:license", {"rdf:resource": lic.url})
    return md


def licence_text(licences: list[Licence]) -> str:
    """Plain text listing the licences of the parts of an image."""
    return "\n".join(["Made with WYLTKM. Licences of the parts of this image:",
                      *(f"- {lic.text()}" for lic in licences)])


def render_svg(library: Library, request: Request) -> Result:
    """Render ``request`` as SVG. Raises ``UnknownDesign``, ``UnknownIcon``,
    ``InvalidRequest`` or ``DataError``."""
    design = library.design(request.design)
    colours = design.colours(request.scheme)
    parts = _Parts()
    parts.licence(design.licence)

    icon = _icon(library, request, design, colours["icon"], parts)
    q = qrmod.paths(request.content, design.qr, with_hole=icon is not None)
    n = q.size

    top = None
    if request.lines:
        lines = [[textmod.Run(line)] for line in request.lines]
        top = _text_block(library, design, design.top_style(request.scheme), lines, n, parts)

    bottom_text = bottom_svg = None
    if design.bottom.type == "text":
        bottom_text = _text_block(library, design, design.bottom_style(request.scheme),
                                  [list(line) for line in design.bottom.lines], n, parts)
    elif design.bottom.type == "svg":
        bottom_svg = svgmod.normalise(
            design.bottom.svg.read_bytes(), id_prefix="bottom-",
            recolour=colours["bottom"] if design.bottom.recolour else None,
            where=f"design {design.name} bottom")
        parts.warnings.extend(bottom_svg.warnings)

    border = BORDER if (request.border if request.border is not None
                        else design.defaults.border) else 0
    background = (request.background if request.background is not None
                  else design.defaults.background)

    # Layout in module units, top to bottom.
    body: list[ET.Element] = []
    y = float(border)
    if top is not None:
        body.append(_paths_group(top, border, y, colours["top"], colours["top"]))
        y += top.height + design.top_style(request.scheme).gap
    qr_y = y
    g = ET.Element("g", transform=f"translate({num(border)} {num(qr_y)})")
    if q.modules:
        ET.SubElement(g, "path", d=q.modules, fill=colours["modules"])
    ET.SubElement(g, "path", {"d": q.rings, "fill": colours["finder_ring"],
                              "fill-rule": "evenodd"})
    ET.SubElement(g, "path", d=q.centres, fill=colours["finder_centre"])
    if icon is not None:
        box = q.hole - 1
        start = (n - box) / 2
        g.append(svgmod.place(icon, start, start, box, box))
    body.append(g)
    y += n
    if bottom_text is not None:
        y += design.bottom_style(request.scheme).gap
        body.append(_paths_group(bottom_text, border, y, colours["bottom"],
                                 colours["highlight"]))
        y += bottom_text.height
    elif bottom_svg is not None:
        y += design.bottom_style(request.scheme).gap
        h = n * bottom_svg.aspect
        body.append(svgmod.place(bottom_svg, border, y, n, h))
        y += h
    main_bottom = y
    y += border

    side_w = 0.0
    if request.side:
        if request.side_font is not None:
            path = library.pickable_fonts().get(request.side_font)
            if path is None:
                raise InvalidRequest(f"font {request.side_font} is not available for the side text")
            font = library.fonts.load(path)
        else:
            font = library.fonts.resolve(design.side_fonts(request.scheme), list(design.dirs), parts.warnings)
        length = main_bottom - border
        sb = sidemod.block(font.font, request.content, length, design.side.min_size,
                           design.side.max_size, design.side.max_columns, parts.warnings)
        if sb is not None:
            parts.licence(font.licence)
            x0 = border + n + design.side.gap
            if design.side.direction == "up":
                transform = f"translate({num(x0)} {num(border + length)}) rotate(-90)"
            else:
                transform = f"translate({num(x0 + sb.height)} {num(border)}) rotate(90)"
            g = ET.Element("g", transform=transform)
            ET.SubElement(g, "path", d=sb.normal, fill=colours["side"])
            body.append(g)
            side_w = design.side.gap + sb.height

    total_w = n + side_w + 2 * border
    total_h = y
    width = request.width
    height = round(width * total_h / total_w, 3)

    root = ET.Element("svg", {
        "xmlns": svgmod.SVG_NS,
        "width": num(width),
        "height": num(height),
        "viewBox": f"0 0 {num(total_w)} {num(total_h)}",
    })
    parts.licences.sort()
    if request.licence_metadata:
        root.append(_metadata(parts.licences))
    if background:
        ET.SubElement(root, "path", d=f"M0 0H{num(total_w)}V{num(total_h)}H0Z",
                      fill=colours["background"])
    root.extend(body)
    ET.indent(root, space="")
    svg = ET.tostring(root, encoding="unicode", xml_declaration=False)
    svg = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg + "\n"
    return Result(svg=svg, width=width, height=height, warnings=parts.warnings,
                  licences=parts.licences, modules=n)


def render_icon(library: Library, name: str, colour: str | None = None) -> str:
    """A single icon as a standalone SVG (normalised, paths only), recoloured
    with ``colour`` if given and the source recolours this icon."""
    src, n = library.icon(name, colour)
    vx, vy, vw, vh = n.viewbox
    root = ET.Element("svg", {"xmlns": svgmod.SVG_NS,
                              "viewBox": f"{num(vx)} {num(vy)} {num(vw)} {num(vh)}"})
    root.append(n.group)
    ET.indent(root, space="")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            + ET.tostring(root, encoding="unicode") + "\n")


def _png_text_chunk(png: bytes, keyword: str, text: str) -> bytes:
    """Insert an iTXt chunk (UTF-8 text) before IEND."""
    data = keyword.encode("latin-1") + b"\0\0\0\0\0" + text.encode("utf-8")
    chunk = struct.pack(">I", len(data)) + b"iTXt" + data
    chunk += struct.pack(">I", zlib.crc32(b"iTXt" + data) & 0xFFFFFFFF)
    iend = png.rindex(b"IEND") - 4
    return png[:iend] + chunk + png[iend:]


def render_png(library: Library, request: Request) -> Result:
    """Render ``request`` as PNG (the SVG rasterised). ``result.png`` holds
    the image; ``result.svg`` the SVG it was made from."""
    result = render_svg(library, request)
    png = cairosvg.svg2png(bytestring=result.svg.encode("utf-8"), output_width=result.width)
    if request.licence_metadata:
        png = _png_text_chunk(png, "Copyright", licence_text(result.licences))
    result.png = png
    return result
