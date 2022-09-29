import urllib.parse

from flask import render_template, request

from wyltkm.forms import ConfigForm


def index():
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
