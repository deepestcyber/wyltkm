"""The WYLTKM web app (Flask). Run with ``wyltkm web`` for development, or
with a WSGI server: ``gunicorn 'wyltkm.web:create_app()'``."""

from __future__ import annotations

import io
import urllib.parse

from flask import Flask, Response, abort, jsonify, render_template, request, send_file
from slugify import slugify

from wyltkm import __version__
from wyltkm.core import (InvalidRequest, Library, Request, UnknownDesign, UnknownIcon,
                         WebConfig, WyltkmError, render_png, render_svg)
from wyltkm.core.request import DEFAULT_WIDTH, NO_ICON

APP_INFO = {
    "version": __version__,
    "source": "https://github.com/deepestcyber/wyltkm",
    "info": "https://wiki.attraktor.org/Would_you_like_to_know_more%3F",
}
DEFAULT_CONTENT = "https://wiki.attraktor.org"
PARAMS = ("content", "text", "design", "scheme", "icon", "width", "border", "background",
          "licence_metadata")


def _flag(value: str | None, name: str) -> bool | None:
    if value is None or value == "":
        return None
    if value in ("1", "0"):
        return value == "1"
    raise InvalidRequest(f"{name} must be 1 or 0")


def request_from(values, files=None, default_content: str | None = None,
                 web: WebConfig = WebConfig()) -> Request:
    """Build a core ``Request`` from query or form values."""
    content = values.get("content") or default_content or ""
    width = values.get("width") or str(DEFAULT_WIDTH)
    try:
        width = int(width)
    except ValueError:
        raise InvalidRequest("width must be a whole number") from None
    if width > web.max_width:
        raise InvalidRequest(f"width must be at most {web.max_width}")
    icon_svg = None
    if files is not None and files.get("icon_file") and files["icon_file"].filename:
        icon_svg = files["icon_file"].read(web.max_upload_bytes + 1)
        if len(icon_svg) > web.max_upload_bytes:
            raise InvalidRequest(f"icon file is larger than {web.max_upload_bytes} bytes")
    metadata = _flag(values.get("licence_metadata"), "licence_metadata")
    return Request(
        content=content,
        text=values.get("text", ""),
        design=values.get("design") or None,
        scheme=values.get("scheme") or None,
        icon=values.get("icon") or None,
        icon_svg=icon_svg,
        width=width,
        border=_flag(values.get("border"), "border"),
        background=_flag(values.get("background"), "background"),
        licence_metadata=True if metadata is None else metadata,
    )


def create_app(library: Library | None = None) -> Flask:
    """The Flask app. Without ``library``, it is made from config file and
    environment (``Library.from_config()``)."""
    lib = library or Library.from_config()
    web = lib.config.web if lib.config is not None else WebConfig()
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = web.max_upload_bytes + 64 * 1024

    def error_response(e: WyltkmError):
        status = 404 if isinstance(e, (UnknownDesign, UnknownIcon)) else 400
        return Response(str(e) + "\n", status=status, mimetype="text/plain")

    def icon_names() -> list[str]:
        return [f"{s.name}:{n}" for s in lib.icons.sources() for n in s.names()]

    @app.route("/")
    def index():
        args = {k: v for k, v in request.args.items() if k in PARAMS and v != ""}
        args.setdefault("content", DEFAULT_CONTENT)
        result = error = None
        try:
            req = request_from(args, web=web)
            result = render_svg(lib, req)
            design = lib.design(req.design)
        except WyltkmError as e:
            error = str(e)
            design = None
        img_args = urllib.parse.urlencode(args)
        return render_template("index.html", APP_INFO=APP_INFO, args=args, result=result,
                               error=error, design=design, designs=lib.designs.all(),
                               default_design=lib.default_design, icons=icon_names(),
                               no_icon=NO_ICON, img_args=img_args, max_width=web.max_width)

    def render_route(fmt: str):
        values = request.form if request.method == "POST" else request.args
        try:
            req = request_from(values, request.files if request.method == "POST" else None,
                               web=web)
            result = render_png(lib, req) if fmt == "png" else render_svg(lib, req)
        except WyltkmError as e:
            return error_response(e)
        data = result.png if fmt == "png" else result.svg.encode("utf-8")
        mimetype = "image/png" if fmt == "png" else "image/svg+xml"
        download = values.get("download") == "1"
        name = slugify(req.text) if req.text.strip() else "wyltkm-qr"
        return send_file(io.BytesIO(data), mimetype=mimetype, as_attachment=download,
                         download_name=f"{name or 'wyltkm-qr'}.{fmt}")

    @app.route("/render.svg", methods=["GET", "POST"])
    def render_svg_route():
        return render_route("svg")

    @app.route("/render.png", methods=["GET", "POST"])
    def render_png_route():
        return render_route("png")

    @app.route("/api/licences")
    def api_licences():
        try:
            result = render_svg(lib, request_from(request.args, web=web))
        except WyltkmError as e:
            return error_response(e)
        return jsonify([{
            "part": lic.part, "name": lic.name, "url": lic.url, "holder": lic.holder,
            "attribution": lic.attribution, "requires_attribution": lic.requires_attribution,
        } for lic in result.licences])

    @app.route("/licences")
    def licences_page():
        designs = []
        for name in lib.designs.names():
            try:
                designs.append(lib.designs.get(name).licence)
            except WyltkmError:
                pass
        return render_template("licences.html", APP_INFO=APP_INFO, designs=designs,
                               sources=[s.licence for s in lib.icons.sources()])

    @app.route("/help")
    def help_page():
        return render_template("help.html", APP_INFO=APP_INFO)

    @app.errorhandler(413)
    def too_large(_):
        return Response("upload too large\n", status=413, mimetype="text/plain")

    return app
