import io

import qrcode
import qrcode.image.svg
import svgwrite
from reportlab.graphics.renderSVG import SVGCanvas, draw
from reportlab.graphics.renderPM import drawToFile
from svglib.svglib import svg2rlg
from reportlab.graphics.shapes import Drawing


def generate_qr(text):
    # factory = qrcode.image.svg.SvgPathImage
    # factory = qrcode.image.svg.SvgImage
    factory = qrcode.image.svg.SvgFragmentImage
    img = qrcode.make(text, image_factory=factory, border=0)
    stream = io.BytesIO()
    img.save(stream)
    stream.seek(0)
    qr = svg2rlg(stream)
    return qr


def generate_head(text):
    d = svgwrite.Drawing("head.svg", (100, 13))
    p = d.add(d.g(font_size="15px"))
    t = d.text(text, (50, 13), style="text-anchor:middle")
    p.add(t)
    stream = io.StringIO()
    d.write(stream)
    stream.seek(0)
    mem = io.BytesIO()
    mem.write(stream.getvalue().encode())
    mem.seek(0)
    head = svg2rlg(mem)
    return head


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
    drawToFile(d, stream, "PNG")
    stream.seek(0)
    return stream


def generate_tb(content, *, width=None):
    if width is None:
        width = 1000
    top_space = width * 0.05
    bot_space = width * 0.05

    qr = generate_qr(content)
    resize_to_width(qr, width)

    top = svg2rlg("static/wyltkm-first-line.svg")
    resize_to_width(top, width)

    bot = svg2rlg("static/wyltkm-second-line.svg")
    resize_to_width(bot, width)

    move(top, 0, qr.height + bot.height + bot_space + top_space)
    move(qr, 0, bot.height + bot_space)

    d = Drawing(width, qr.height + top.height + bot.height + bot_space + top_space)
    d.add(qr)
    d.add(top)
    d.add(bot)
    return d


def generate_bot(content, *, head=None, width=None):
    if width is None:
        width = 1000
    if head is None:
        head_space = 0.0
        head_height = 0.0
    else:
        head_space = width * 0.05
        head = generate_head(head)
        resize_to_width(head, width)
        head_height = head.height

    bot_space = width * 0.05

    qr = generate_qr(content)
    resize_to_width(qr, width)

    bot = svg2rlg("static/wyltkm-two-lines.svg")
    resize_to_width(bot, width)

    move(qr, 0, bot.height + bot_space)

    d = Drawing(width, qr.height + bot.height + bot_space + head_space + head_height)
    if head is not None:
        move(head, 0, bot.height + bot_space + qr.height + head_space)
        d.add(head)
    d.add(qr)
    d.add(bot)
    return d
