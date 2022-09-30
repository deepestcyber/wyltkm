import os
import urllib.parse

from flask import Flask, render_template, request, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, IntegerField

from . import generate


class ConfigForm(FlaskForm):
    """Form used for configuring the qr-code to create."""
    k = RadioField("Kind", choices=[
        ("r", "raw"),
        ("b", "bottom"),
        ("tb", "top/bottom"),
    ], default="b")
    c = StringField("Content")
    h = StringField("Heading")
    f = RadioField("Format", choices=[
        ("svg", "SVG"),
        ("png", "PNG"),
    ], default="svg")
    w = IntegerField("Width")
    submit = SubmitField("generate")


app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(32)


@app.route("/")
def index():
    """View for index page, that shows the form and preview for qr codes."""
    form = ConfigForm(request.args)
    svg_args = {k: v for k, v in request.args.items() if k in ["k", "c", "h"]}
    img_args = {k: v for k, v in request.args.items() if k in ["k", "c", "h"]}
    img_args["f"] = "png"
    img_args["w"] = 300
    return render_template("index.html",
                           form=form,
                           img_args=urllib.parse.urlencode(img_args),
                           svg_args=urllib.parse.urlencode(svg_args),
                           )


@app.route("/img")
def img_route():
    """View that creates images containing qr codes."""
    content = request.args.get("c", "WOULD YOU LIKE TO KNOW MORE?")
    head = request.args.get("h")
    if head == "":
        head = None
    fmt = request.args.get("f", "svg")
    width = request.args.get("w")
    if width == "":
        width = None
    if width is not None:
        width = int(width)

    kind = request.args.get("k", "b")
    if kind == "tb":
        qr = generate.generate_tb(content, width=width)
    else:
        qr = generate.generate_bot(content, width=width, head=head)

    if fmt == "png":
        return send_file(generate.drawing_to_png_stream(qr), mimetype="image/png")
    else:
        return send_file(generate.drawing_to_svg_stream(qr), mimetype="image/svg+xml")
