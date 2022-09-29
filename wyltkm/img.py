import io
from flask import request, send_file

from wyltkm.forms import ConfigForm


def img():
    from . import generate

    form = ConfigForm(request.args)

    content = request.args.get("c", "WOULD YOU LIKE TO KNOW MORE?")
    head = request.args.get("h")
    fmt = request.args.get("f", "svg")
    width = request.args.get("w")
    if width is not None:
        width = int(width)

    kind = request.args.get("k", "b")
    if kind == "tb":
        qr = generate.generate_tb(content, width=width)
    else:
        qr = generate.generate_bot(content, head, width=width)

    if fmt == "png":
        return send_file(generate.drawing_to_png_stream(qr), mimetype="image/png")
    else:
        return send_file(generate.drawing_to_svg_stream(qr), mimetype="image/svg+xml")
