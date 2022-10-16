import io
import importlib.resources
import os.path

import qrcode
import qrcode.image.svg
from qrcode.image.svg import ET
from reportlab.graphics.renderSVG import SVGCanvas, draw
from svglib.svglib import svg2rlg
from reportlab.graphics.shapes import Drawing
from cairosvg import svg2png


class NotJustDots(qrcode.image.svg.SvgFragmentImage):
    """
    Standalone SVG image builder

    Creates a QR-code image as a standalone SVG document.
    """
    background = None

    def _add_corner(self, svg, x, y):
        svg.append(
            ET.Element(
                "circle", cx=self.units(x), cy=self.units(y),
                r=self.units(self.box_size * 1.5),
            )
        )
        svg.append(
            ET.Element(
                "circle", cx=self.units(x), cy=self.units(y),
                r=self.units(self.box_size * 3),
                stroke="black",
                fill="none",
                **{"stroke-width": self.units(self.box_size)},
            )
        )

    def _svg(self, tag='svg', **kwargs):
        svg = super()._svg(tag=tag, **kwargs)
        svg.set("xmlns", self._SVG_namespace)
        if self.background:
            svg.append(
                ET.Element(
                    'rect', fill=self.background, x='0', y='0', width='100%',
                    height='100%'))
        # tl
        self._add_corner(svg, x=self.box_size * (self.border + 3.5), y=self.box_size * (self.border + 3.5))
        self._add_corner(svg, x=self.box_size * (self.width + self.border - 3.5), y=self.box_size * (self.border + 3.5))
        self._add_corner(svg, x=self.box_size * (self.border + 3.5), y=self.box_size * (self.width + self.border - 3.5))
        return svg

    def drawrect(self, row, col):
        x, y = self.pixel_box(row, col)[0]
        x += self.box_size/2
        y += self.box_size/2

        corner = None
        if row < 7 and col < 7:
            corner = "ul"
        elif row < 7 and col >= self.width - 7:
            corner = "ur"
        elif row >= self.width - 7 and col < 7:
            corner = "lr"

        elem = None
        if corner is None:
            elem = ET.Element(
                "circle", cx=self.units(x), cy=self.units(y),
                r=self.units(self.box_size/2),
            )
        if elem is not None:
            self._img.append(elem)

    def _write(self, stream):
        ET.ElementTree(self._img).write(stream, encoding="UTF-8",
                                        xml_declaration=True)


BLUE = "#67b8dc"
DARK_GRAY = "#4b4b4d"
LIGHT_GREY = "#9b9c9e"


class Roundy(qrcode.image.svg.SvgFragmentImage):
    """
    Standalone SVG image builder

    Creates a QR-code image as a standalone SVG document.
    """
    background = None
    inner_circle_color = "black"
    outer_circle_color = "black"
    dots_color = "black"

    def _add_corner(self, svg, x, y):
        svg.append(
            ET.Element(
                "rect",
                x=self.units(x - self.box_size * 1.5),
                y=self.units(y - self.box_size * 1.5),
                width=self.units(self.box_size * 3),
                height=self.units(self.box_size * 3),
                rx=self.units(self.box_size),
                fill=self.inner_circle_color,
            )
        )
        svg.append(
            ET.Element(
                "rect",
                x=self.units(x - self.box_size * 3),
                y=self.units(y - self.box_size * 3),
                width=self.units(self.box_size * 6),
                height=self.units(self.box_size * 6),
                rx=self.units(self.box_size),
                stroke=self.outer_circle_color,
                fill="none",
                **{"stroke-width": self.units(self.box_size)},
            )
        )

    def _svg(self, tag='svg', **kwargs):
        svg = super()._svg(tag=tag, **kwargs)
        svg.set("xmlns", self._SVG_namespace)
        if self.background:
            svg.append(
                ET.Element(
                    'rect', fill=self.background, x='0', y='0', width='100%',
                    height='100%'))
        # tl
        self._add_corner(svg, x=self.box_size * (self.border + 3.5), y=self.box_size * (self.border + 3.5))
        self._add_corner(svg, x=self.box_size * (self.width + self.border - 3.5), y=self.box_size * (self.border + 3.5))
        self._add_corner(svg, x=self.box_size * (self.border + 3.5), y=self.box_size * (self.width + self.border - 3.5))
        return svg

    def drawrect(self, row, col):
        x, y = self.pixel_box(row, col)[0]

        corner = None
        if row < 7 and col < 7:
            corner = "ul"
        elif row < 7 and col >= self.width - 7:
            corner = "ur"
        elif row >= self.width - 7 and col < 7:
            corner = "lr"

        elem = None
        if corner is None:
            elem = ET.Element(
                "rect", x=self.units(x), y=self.units(y),
                width=self.unit_size, height=self.unit_size,
                rx=self.units(3),
                fill=self.dots_color,
            )
        if elem is not None:
            self._img.append(elem)

    def _write(self, stream):
        ET.ElementTree(self._img).write(stream, encoding="UTF-8",
                                        xml_declaration=True)


def generate_qr(text, factory=None):
    if factory is None:
        factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(text, image_factory=factory, border=0)
    bots = img.width
    stream = io.BytesIO()
    img.save(stream)
    stream.seek(0)
    qr = svg2rlg(stream)
    return qr, bots


def text_to_rlg(font, text, color):
    svg_src = font.text(text, color=color, halign="center").svg()
    # remove broken empty auto-closing path that break PNG generation
    svg_src = svg_src.replace('<path d="Z " />', '')
    stream = io.StringIO()
    stream.write(svg_src)
    stream.seek(0)
    mem = io.BytesIO()
    mem.write(stream.getvalue().encode())
    mem.seek(0)
    rlg = svg2rlg(mem)
    return rlg


def get_font(what):
    import ziafont
    ziafont.config.svg2 = False
    if what == "p":
        font_path = "/home/kratenko/git/wyltkm/tinker/PhutureODCBlack.ttf"
        font_path = "PhutureODCBlack.ttf"
    elif what == "a":
        font_path = "/home/kratenko/git/wyltkm/tinker/AgencyFB-Bold.ttf"
        font_path = "AgencyFB-Bold.ttf"
    else:
        font_path = None

    if font_path and os.access(font_path, os.R_OK):
        font = ziafont.Font(font_path)
    else:
        font = ziafont.Font()
    return font


def generate(content, *, width=None, top=None, top_text=None, bot=None, bot_text=None, kind=None, color=None,
             border=None):
    from . import res
    if width is None:
        width = 250
    else:
        width = int(width)

    # select color schema
    if color == "a":
        text_color_name = "dark"
        text_color = DARK_GRAY
        dots_color = LIGHT_GREY
        outer_circle_color = BLUE
        inner_circle_color = DARK_GRAY
    else:
        text_color_name = "black"
        text_color = "black"
        dots_color = "black"
        outer_circle_color = "black"
        inner_circle_color = "black"

    # Generate QR-Code image:
    if kind == "a":
        factory = Roundy
        factory.outer_circle_color = outer_circle_color
        factory.inner_circle_color = inner_circle_color
        factory.dots_color = dots_color
        qr, qr_squares = generate_qr(content, factory=factory)
    else:
        qr, qr_squares = generate_qr(content)
    if border == "4":
        total_squares = qr_squares + 8
    else:
        total_squares = qr_squares
    square_width = width / total_squares
    content_width = square_width * qr_squares
    border_width = (total_squares - qr_squares) * square_width / 2

    # Generate Bottom image:
    bot_img = None
    if bot == "au":
        f = importlib.resources.open_text(res, f"wyltkm-agency-upper-{text_color_name}.svg")
        bot_img = svg2rlg(f)
    elif bot == "al":
        f = importlib.resources.open_text(res, f"wyltkm-agency-lower-{text_color_name}.svg")
        bot_img = svg2rlg(f)
    elif bot == "pu":
        f = importlib.resources.open_text(res, f"wyltkm-phuture-upper-{text_color_name}.svg")
        bot_img = svg2rlg(f)
    elif bot == "a":
        font = get_font("a")
        bot_img = text_to_rlg(font, bot_text, text_color)
    elif bot == "p":
        font = get_font("p")
        bot_img = text_to_rlg(font, bot_text, text_color)

    # Generate Top image:
    top_img = None
    if top_text and top != "b":
        font = get_font(top)
        top_img = text_to_rlg(font, top_text, text_color)

    # Connect all parts:
    total_height = border_width
    if bot_img:
        resize_to_width(bot_img, content_width)
        move(bot_img, border_width, total_height)
        total_height += bot_img.height
        bot_space = square_width * 3
        total_height += bot_space

    resize_to_width(qr, content_width)
    move(qr, border_width, total_height)
    total_height += qr.height

    if top_img:
        resize_to_width(top_img, content_width)
        total_height += 2 * square_width
        move(top_img, border_width, total_height)
        total_height += top_img.height

    total_height += border_width

    d = Drawing(width, total_height)
    d.add(qr)
    if top_img:
        d.add(top_img)
    if bot_img:
        d.add(bot_img)
    return d


def resize_to_width(d, w):
    """
    Scale a rlg drawing to a fixed destination width and update drawings size.
    """
    ratio = w / d.width
    d.scale(ratio, ratio)
    d.width *= ratio
    d.height *= ratio


def move(d, dx, dy):
    """
    Translate a rlg drawing, respecting the current scaling.
    """
    d.translate(dx / d.transform[0], dy / d.transform[3])


def drawing_to_svg_stream(d):
    c = SVGCanvas((d.width, d.height))
    draw(d, c, 0, 0)
    stream = io.StringIO()
    c.save(stream)
    stream.seek(0)

    mem = io.BytesIO()
    mem.write(stream.getvalue().encode())
    mem.seek(0)
    return mem


def drawing_to_png_stream(d):
    stream = io.BytesIO()
    svg2png(file_obj=drawing_to_svg_stream(d), write_to=stream)
    stream.seek(0)
    return stream
