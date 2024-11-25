import importlib.resources
import os
import re
import urllib.parse

from flask import Flask, render_template, request, send_file, Response, abort
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, IntegerField, TextAreaField
from slugify import slugify

from . import generate
from .generate import WYLTKM

APP_INFO = {
    "version": "0.2.0",
    "source": "https://github.com/deepestcyber/wyltkm",
    "info": "https://wiki.attraktor.org/Would_you_like_to_know_more%3F",
}

ICONS = [
    "",
    "attraktor",
    "attraktor-mono",
    "bell-solid",
    "biohazard-solid",
    "bolt-lightning-solid",
    "book-solid",
    "bus-solid",
    "cat-solid",
    "circle-info-solid",
    "circle-question-solid",
    "computer-solid",
    "flask-vial-solid",
    "gamepad-solid",
    "gavel-solid",
    "hammer-solid",
    "heart-solid",
    "industry-solid",
    "kitchen-set-solid",
    "leaf-solid",
    "lightbulb-solid",
    "microscope-solid",
    "mug-hot-solid",
    "music-solid",
    "network-wired-solid",
    "paperclip-solid",
    "person-digging-solid",
    "print-solid",
    "puzzle-piece-solid",
    "qrcode-solid",
    "radiation-solid",
    "radio-solid",
    "restroom-solid",
    "road-bridge-solid",
    "road-solid",
    "robot-solid",
    "rocket-solid",
    "screwdriver-wrench-solid",
    "sliders-solid",
    "sun-solid",
    "toilet-paper-solid",
    "toilet-solid",
    "tower-broadcast-solid",
    "tower-cell-solid",
    "train-subway-solid",
    "trash-can-solid",
    "utensils-solid",
    "walkie-talkie-solid",
    "warehouse-solid",
    "wifi-solid",

    "bluesky-brands-solid",
    "github-brands-solid",
    "mastodon-brands-solid",

    "carbon/aperture",
    "carbon/binoculars",
    "carbon/boot",
    "carbon/bot",
    "carbon/box",
    "carbon/drone--front",
    "carbon/game--console",
    "carbon/help",
    "carbon/identification",
    "carbon/information",
    "carbon/police",
    "carbon/settings",
    "carbon/stamp",
    "carbon/theater",
    "carbon/video",
    "carbon/warning--alt",
]

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
            ("b", "Attraktor Black/White"),
            ("38c3", "38c3"),
        ],
        default="a",
    )
    g = RadioField(
        "Background",
        choices=[
            ("w", "Colour"),
            ("", "Transparent"),
        ],
        default="w",
    )
    B = RadioField(
        "Border",
        choices=[
            ("4", "Yes"),
            ("0", "No"),
        ],
        default="0",
    )
    i = RadioField(
        "Icon",
        choices=[
            (n, n if n else "None") for n in ICONS
        ],
        default="",
    )
    w = IntegerField("Width", default=250)
    preview = SubmitField("preview")
    exp = SubmitField("adv. parameter", render_kw={"formaction": "exp"})
    svg = SubmitField("SVG", render_kw={"formaction": "img"})
    png = SubmitField("PNG", render_kw={"formaction": "img"})


app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(32)


@app.route("/help")
def help():
    return render_template("help.html", APP_INFO=APP_INFO)


@app.route("/")
def index():
    """View for index page, that shows the form and preview for qr codes."""
    form = ConfigForm(request.args)
    svg_args = {k: v for k, v in request.args.items() if k in ["t", "tt", "q", "c", "b", "bt", "C", "w", "B", "i", "g"]}
    img_args = {k: v for k, v in request.args.items() if k in ["t", "tt", "q", "c", "b", "bt", "C", "w", "B", "i", "g"]}
    img_args["png"] = "PNG"
    img_args["w"] = "250"
    return render_template("index.html",
                           form=form,
                           img_args=urllib.parse.urlencode(img_args),
                           svg_args=urllib.parse.urlencode(svg_args),
                           APP_INFO=APP_INFO,
                           dir=dir,
                           ttype=type,
                           )


@app.route("/exp")
def exp():
    """View for index page, that shows the form and preview for qr codes."""
    form = ConfigForm(request.args)
    svg_args = {k: v for k, v in request.args.items() if k in ["t", "tt", "q", "c", "b", "bt", "C", "w", "B", "i", "g"]}
    img_args = {k: v for k, v in request.args.items() if k in ["t", "tt", "q", "c", "b", "bt", "C", "w", "B", "i", "g"]}
    img_args["png"] = "PNG"
    img_args["w"] = "250"
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

    if form.C.data == "38c3":
        st = generate.style.ccc38c3
    elif form.C.data == "b":
        st = generate.style.black_on_white
    else:
        st = generate.style.attraktor
    wyl = WYLTKM()
    wyl.style = st
    wyl.icon = form.i.data
    wyl.transparent = form.g.data == ""
    wyl.border = form.B.data == "4"
    wyl.width = form.w.data
    wyl.text = form.tt.data
    wyl.content = form.c.data
    qr = wyl.generate()

#    qr = generate.generate(
#        form.c.data,
#        width=form.w.data,
#        top=form.t.data,
#        top_text=form.tt.data,
#        bot=form.b.data,
#        bot_text=form.bt.data,
#        kind=form.q.data,
#        color=form.C.data,
#        border=form.B.data,
#        icon=form.i.data,
#        background=form.g.data,
#    )
    if form.tt.data:
        dl_name = slugify(form.tt.data)
    else:
        dl_name = "wyltkm-qr"
    if form.png.data:
        return send_file(
            generate.drawing_to_png_stream(qr),
            mimetype="image/png",
            download_name=f"{dl_name}.png",
        )
    else:
        return send_file(
            generate.drawing_to_svg_stream(qr),
            mimetype="image/svg+xml",
            download_name=f"{dl_name}.svg"
        )


class IconForm(FlaskForm):
    i = StringField("Icon", default="", render_kw={"list": "icons"})
    c = StringField("Colour", default="")

@app.route("/icon")
def icon():
    form = ConfigForm(request.args)
    from wyltkm.icon import load_icon
    f = load_icon(form.i.data, form.c.data or None)
    if f is None:
        abort(404)
    return Response(
        f,
        mimetype = "image/svg+xml",
    )


