"""The WYLTKM web app (Flask). Run with ``wyltkm web`` for development, or
with a WSGI server: ``gunicorn 'wyltkm.web:create_app()'``."""

from __future__ import annotations

import functools
import hashlib
import re
import urllib.parse

from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from slugify import slugify

from wyltkm import __version__
from wyltkm.core import (InvalidRequest, Library, Request, UnknownDesign, UnknownIcon,
                         WebConfig, WyltkmError, render_icon, render_png, render_svg)
from wyltkm.core.fonts import BUNDLED_DIR
from wyltkm.core.licences import for_font
from wyltkm.core.request import DEFAULT_WIDTH, NO_ICON, preview_request

APP_INFO = {
    "version": __version__,
    "source": "https://github.com/deepestcyber/wyltkm",
    "info": "https://wiki.attraktor.org/Would_you_like_to_know_more%3F",
}
DEFAULT_CONTENT = "https://wiki.attraktor.org"
PARAMS = ("content", "text", "design", "scheme", "icon", "width", "border", "background",
          "licence_metadata", "side", "side_font")
UI_FONTS = {"SpaceGrotesk-Regular.otf", "Hack-Regular.ttf"}
"""Bundled fonts the web page itself uses."""
CACHE_SECONDS = 3600
BROWSE_PAGE = 120
COLOUR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


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
        side=bool(_flag(values.get("side"), "side")),
        side_font=values.get("side_font") or None,
    )


def _cached(data: bytes, mimetype: str, max_age: int = CACHE_SECONDS) -> Response:
    """Response with ETag and cache time; answers 304 when the client has it.
    Output is deterministic, so a hash of it is a good ETag."""
    resp = Response(data, mimetype=mimetype)
    resp.set_etag(hashlib.sha256(data).hexdigest()[:32])
    resp.cache_control.public = True
    resp.cache_control.max_age = max_age
    return resp.make_conditional(request)


def _licence_json(lic) -> dict:
    return {"part": lic.part, "name": lic.name, "url": lic.url, "holder": lic.holder,
            "attribution": lic.attribution, "requires_attribution": lic.requires_attribution}


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

    def designs_info() -> list[dict]:
        """Designs for the picker, the default design first."""
        out = []
        for d in lib.ordered_designs():
            name = d.name
            base = f"/designs/{name}/preview.svg"
            out.append({
                "name": d.name, "title": d.title, "description": d.description,
                "default": name == lib.default_design,
                "colours": d.colours(),
                "default_scheme": d.default_scheme,
                "default_icon": d.defaults.icon,
                "schemes": [{"name": s.name, "title": s.title, "colours": s.colours,
                             "icon": d.default_icon(s.name),
                             "preview": f"{base}?scheme={s.name}"} for s in d.schemes.values()],
                "preview": base,
                "licence": {"name": d.licence.name, "url": d.licence.url,
                            "holder": d.licence.holder},
            })
        return out

    @app.route("/")
    def index():
        args = {k: v for k, v in request.args.items() if k in PARAMS and v != ""}
        args.setdefault("content", DEFAULT_CONTENT)
        result = error = design = None
        try:
            req = request_from(args, web=web)
            design = lib.design(req.design)
            result = render_svg(lib, req)
        except WyltkmError as e:
            error = str(e)
        icon_q = request.args.get("icon_q", "").strip()
        icon_source = request.args.get("icon_source", "")
        try:
            icon_hits = (lib.icons.search(icon_q, icon_source or None, limit=64)
                         if icon_q else [])
        except WyltkmError:
            icon_hits = []
        icon_colour = "#85858b"
        tile_bg = "transparent"
        scheme = None
        if design is not None:
            scheme = args.get("scheme") or design.default_scheme
            try:
                icon_colour = design.colours(args.get("scheme"))["icon"]
                tile_bg = design.colours(args.get("scheme"))["background"]
            except WyltkmError:
                pass
        current_icon = NO_ICON
        if args.get("icon"):
            current_icon = args["icon"]
        elif design is not None:
            try:
                current_icon = design.default_icon(args.get("scheme"))
            except WyltkmError:
                pass
        return render_template(
            "index.html", APP_INFO=APP_INFO, args=args, result=result, error=error,
            design=design, scheme=scheme, designs=designs_info(),
            default_design=lib.default_design, icon_q=icon_q, icon_source=icon_source,
            icon_sources=lib.icons.sources(), icon_hits=icon_hits, icon_colour=icon_colour,
            tile_bg=tile_bg,
            current_icon=current_icon,
            side_fonts=list(lib.pickable_fonts()) if args.get("side") == "1" else [],
            no_icon=NO_ICON, query=urllib.parse.urlencode(args), max_width=web.max_width,
            max_upload_bytes=web.max_upload_bytes)

    def render_route(fmt: str):
        post = request.method == "POST"
        values = request.form if post else request.args
        try:
            req = request_from(values, request.files if post else None, web=web)
            result = render_png(lib, req) if fmt == "png" else render_svg(lib, req)
        except WyltkmError as e:
            return error_response(e)
        data = result.png if fmt == "png" else result.svg.encode("utf-8")
        mimetype = "image/png" if fmt == "png" else "image/svg+xml"
        resp = Response(data, mimetype=mimetype) if post else _cached(data, mimetype)
        name = (slugify(req.text) if req.text.strip() else "") or "wyltkm-qr"
        disposition = "attachment" if values.get("download") == "1" else "inline"
        resp.headers["Content-Disposition"] = f'{disposition}; filename="{name}.{fmt}"'
        return resp

    @app.route("/render.svg", methods=["GET", "POST"])
    def render_svg_route():
        return render_route("svg")

    @app.route("/render.png", methods=["GET", "POST"])
    def render_png_route():
        return render_route("png")

    @app.route("/api/render-info", methods=["GET", "POST"])
    def api_render_info():
        """Size, warnings and licences of the image for the given values."""
        post = request.method == "POST"
        try:
            req = request_from(request.form if post else request.args,
                               request.files if post else None, web=web)
            result = render_svg(lib, req)
        except WyltkmError as e:
            return error_response(e)
        return jsonify({"width": result.width, "height": result.height,
                        "modules": result.modules, "warnings": result.warnings,
                        "licences": [_licence_json(lic) for lic in result.licences]})

    @functools.lru_cache(maxsize=256)
    def preview_svg(name: str, scheme: str | None) -> str:
        design = lib.designs.get(name)
        return render_svg(lib, preview_request(name, scheme, design.title)).svg

    @app.route("/designs/<name>/preview.svg")
    def design_preview(name):
        try:
            svg = preview_svg(name, request.args.get("scheme") or None)
        except WyltkmError as e:
            return error_response(e)
        return _cached(svg.encode("utf-8"), "image/svg+xml")

    @app.route("/api/designs")
    def api_designs():
        return jsonify(designs_info())

    @app.route("/api/icons")
    def api_icons():
        try:
            limit = int(request.args.get("limit") or 60)
        except ValueError:
            return error_response(InvalidRequest("limit must be a whole number"))
        limit = max(1, min(limit, 500))
        try:
            hits = lib.icons.search(request.args.get("q", ""), request.args.get("source") or None,
                                    limit)
        except WyltkmError as e:
            return error_response(e)
        return jsonify([{"name": h.name, "label": h.label,
                         "url": f"/icon/{h.name.replace(':', '/', 1)}.svg"} for h in hits])

    @app.route("/api/icon-sources")
    def api_icon_sources():
        return jsonify([{"name": s.name, "title": s.title, "count": len(s.files),
                         "folders": [{"name": f, "count": c} for f, c in s.folders().items()],
                         "licence": {"name": s.licence.name, "url": s.licence.url,
                                     "requires_attribution": s.licence.requires_attribution}}
                        for s in lib.icons.sources()])

    def browse_args():
        """Query, source, folder and paging of the icon browser."""
        q = request.args.get("q", "").strip()
        source = request.args.get("source") or None
        folder = request.args.get("folder") or None
        try:
            offset = max(0, int(request.args.get("offset") or 0))
            limit = max(1, min(int(request.args.get("limit") or BROWSE_PAGE), 500))
        except ValueError:
            raise InvalidRequest("offset and limit must be whole numbers") from None
        return q, source, folder, offset, limit

    @app.route("/api/icons/browse")
    def api_icons_browse():
        """All icons matching the filters, a page at a time, with the total."""
        try:
            q, source, folder, offset, limit = browse_args()
            hits = lib.icons.find(q, source, folder)
        except WyltkmError as e:
            return error_response(e)
        return jsonify({"total": len(hits), "offset": offset,
                        "hits": [{"name": h.name, "label": h.label,
                                  "url": f"/icon/{h.name.replace(':', '/', 1)}.svg"}
                                 for h in hits[offset:offset + limit]]})

    @app.route("/browse")
    def icons_browse():
        """The icon browser as a page (without JavaScript); a pick leads back
        to the form with all its settings."""
        try:
            q, source, folder, offset, limit = browse_args()
            hits = lib.icons.find(q, source, folder)
        except WyltkmError as e:
            return error_response(e)
        form = {k: v for k, v in request.args.items() if k in PARAMS and k != "icon" and v}
        colour, tile_bg = "#85858b", "transparent"
        try:
            design = lib.design(form.get("design"))
            colour = design.colours(form.get("scheme"))["icon"]
            tile_bg = design.colours(form.get("scheme"))["background"]
        except WyltkmError:
            pass

        def link(**changes):
            args = {**{k: v for k, v in request.args.items() if k not in ("offset",)}, **changes}
            return "/browse?" + urllib.parse.urlencode({k: v for k, v in args.items() if v})

        return render_template(
            "icons_browse.html", APP_INFO=APP_INFO, q=q, source=source, folder=folder,
            hits=hits[offset:offset + limit], total=len(hits), offset=offset, limit=limit,
            sources=lib.icons.sources(), colour=colour, tile_bg=tile_bg, link=link,
            pick=lambda name: "/?" + urllib.parse.urlencode({**form, "icon": name}),
            form=form)

    @app.route("/icon/<source>/<path:name>.svg")
    def icon_svg(source, name):
        colour = request.args.get("colour") or None
        if colour is not None and not COLOUR_RE.match(colour):
            return error_response(InvalidRequest("colour must be #rrggbb"))
        try:
            svg = render_icon(lib, f"{source}:{name}", colour)
        except WyltkmError as e:
            return error_response(e)
        return _cached(svg.encode("utf-8"), "image/svg+xml", max_age=86400)

    @app.route("/api/fonts")
    def api_fonts():
        return jsonify([{"name": name, "title": name.rsplit(".", 1)[0]}
                        for name in lib.pickable_fonts()])

    @app.route("/api/licences")
    def api_licences():
        try:
            result = render_svg(lib, request_from(request.args, web=web))
        except WyltkmError as e:
            return error_response(e)
        return jsonify([_licence_json(lic) for lic in result.licences])

    @app.route("/ui-fonts/<name>")
    def ui_font(name):
        if name not in UI_FONTS:
            return Response("not found\n", status=404, mimetype="text/plain")
        return send_from_directory(BUNDLED_DIR, name, max_age=86400 * 30)

    @app.route("/licences")
    def licences_page():
        designs = []
        for name in lib.designs.names():
            try:
                designs.append(lib.designs.get(name).licence)
            except WyltkmError:
                pass
        fonts = [for_font(path) for path in lib.fonts.available().values()]
        return render_template("licences.html", APP_INFO=APP_INFO, designs=designs,
                               sources=[s.licence for s in lib.icons.sources()], fonts=fonts)

    @app.route("/help")
    def help_page():
        return render_template("help.html", APP_INFO=APP_INFO, max_width=web.max_width)

    @app.errorhandler(413)
    def too_large(_):
        return Response("upload too large\n", status=413, mimetype="text/plain")

    return app
