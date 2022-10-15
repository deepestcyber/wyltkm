import os
import urllib.parse

from flask import Flask, render_template, request, send_file
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, IntegerField, TextAreaField

from . import generate

APP_INFO = {
    "version": "0.1.2",
    "source": "https://github.com/deepestcyber/wyltkm",
    "info": "https://wiki.attraktor.org/Would_you_like_to_know_more%3F",
}


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
        description="The text to render above the QR-Code.",
        render_kw={"cols": 50, "rows": 4, },
    )

    q = RadioField(
        "QR-Code Style",
        choices=[
            ("s", "simple"),
            ("a", "Attraktor"),
        ],
        default="a",
    )
    c = StringField(
        "Content",
        default="https://wiki.attraktor.org",
        description="The data inside the QR-Code; typically a URL.",
        render_kw={"size": 50},
    )

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
        default="0",
    )
    f = RadioField("Format", choices=[
        ("svg", "SVG"),
        ("png", "PNG"),
    ], default="svg")
    w = IntegerField("Width", default=250)
    preview = SubmitField("preview")
    svg = SubmitField("SVG", render_kw={"formaction": "img"})


app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(32)


@app.route("/help")
def help():
    return render_template("help.html", APP_INFO=APP_INFO)


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
                           APP_INFO=APP_INFO,
                           )


@app.route("/exp")
def exp():
    """View for index page, that shows the form and preview for qr codes."""
    form = ConfigForm(request.args)
    svg_args = {k: v for k, v in request.args.items() if k in ["t", "tt", "q", "c", "b", "bt", "C", "w", "B"]}
    img_args = {k: v for k, v in request.args.items() if k in ["t", "tt", "q", "c", "b", "bt", "C", "w", "B"]}
    img_args["f"] = "png"
    return render_template("exp.html",
                           form=form,
                           img_args=urllib.parse.urlencode(img_args),
                           svg_args=urllib.parse.urlencode(svg_args),
                           APP_INFO=APP_INFO,
                           )


@app.route("/img")
def img_route():
    """View that creates images containing qr codes."""
    form = ConfigForm(request.args)

    qr = generate.generate(
        form.c.data,
        width=form.w.data,
        top=form.t.data,
        top_text=form.tt.data,
        bot=form.b.data,
        bot_text=form.bt.data,
        kind=form.q.data,
        color=form.C.data,
        border=form.B.data,
    )
    if form.f.data == "png":
        return send_file(generate.drawing_to_png_stream(qr), mimetype="image/png")
    else:
        return send_file(generate.drawing_to_svg_stream(qr), mimetype="image/svg+xml")
