import os
import urllib.parse

from flask import Flask, render_template, request, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, IntegerField, TextAreaField

from . import generate


class ConfigForm(FlaskForm):
    """Form used for configuring the qr-code to create."""
    t = RadioField(
        "Top type",
        choices=[
            ("b", "empty"),
            ("a", "Text (Agency)"),
            ("p", "Text (Phuture)")
        ],
        default="a",
    )
    tt = TextAreaField(
        "Top text",
        default="",
    )

    q = RadioField(
        "QR-Code Type",
        choices=[
            ("s", "simple"),
            ("a", "Attraktor"),
        ],
        default="a",
    )
    c = StringField("Content")

    b = RadioField(
        "Bottom",
        choices=[
            ("b", "empty"),
            ("a", "Text (Agency)"),
            ("p", "Text (Phuture)"),
            ("au", "WYLTNM? (Agency, upper case)"),
            ("al", "WYLTNM? (Agency, lower case)"),
            ("pu", "WYLTNM? (Phuture, upper case)"),
        ],
        default="au",
    )
    bt = TextAreaField(
        "Bottom Text",
        default="",
    )
    C = RadioField(
        "Colour",
        choices=[
            ("a", "Attraktor"),
            ("b", "Black/White")
        ],
        default="a",
    )
    B = RadioField(
        "Border",
        choices=[
            ("4", "Yes"),
            ("0", "No"),
        ],
        default="4",
    )
    f = RadioField("Format", choices=[
        ("svg", "SVG"),
        ("png", "PNG"),
    ], default="svg")
    w = IntegerField("Width", default=250)
    submit = SubmitField("generate")


app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(32)


@app.route("/")
def index():
    """View for index page, that shows the form and preview for qr codes."""
    form = ConfigForm(request.args)
    svg_args = {k: v for k, v in request.args.items() if k in ["t", "tt", "q", "c", "b", "bt", "C", "w", "B"]}
    img_args = {k: v for k, v in request.args.items() if k in ["t", "tt", "q", "c", "b", "bt", "C", "w", "B"]}
    img_args["f"] = "png"
    return render_template("index.html",
                           form=form,
                           img_args=urllib.parse.urlencode(img_args),
                           svg_args=urllib.parse.urlencode(svg_args),
                           )


@app.route("/img")
def img_route():
    """View that creates images containing qr codes."""
    content = request.args.get("c", "WOULD YOU LIKE TO KNOW MORE?")
    fmt = request.args.get("f", "svg")

    qr = generate.generate(
        content,
        width=request.args.get("w", 250),
        top=request.args.get("t"),
        top_text=request.args.get("tt"),
        bot=request.args.get("b"),
        bot_text=request.args.get("bt"),
        kind=request.args.get("q"),
        color=request.args.get("C"),
        border=request.args.get("B"),
    )
    if fmt == "png":
        return send_file(generate.drawing_to_png_stream(qr), mimetype="image/png")
    else:
        return send_file(generate.drawing_to_svg_stream(qr), mimetype="image/svg+xml")
