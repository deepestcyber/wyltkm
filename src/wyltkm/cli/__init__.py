"""The ``wyltkm`` command line tool."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import click

from wyltkm import __version__
from wyltkm.core import (DataError, InvalidRequest, Library, Request, UnknownDesign,
                         UnknownIcon, WyltkmError, render_icon, render_png, render_svg)
from wyltkm.core.fonts import BUNDLED_DIR, FALLBACK_LICENCE
from wyltkm.core import licences as licmod
from wyltkm.core.designs import MIN_CONTRAST, contrast
from wyltkm.core.request import DEFAULT_WIDTH, MAX_WIDTH, MIN_WIDTH, preview_request

EXIT_INVALID = 1
EXIT_NOT_FOUND = 3
EXIT_DATA = 4


class _Fail(click.ClickException):
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.exit_code = code


_LIBRARY: Library | None = None


def _library() -> Library:
    """The library from config file and environment (created once)."""
    global _LIBRARY
    if _LIBRARY is None:
        try:
            _LIBRARY = Library.from_config()
        except WyltkmError as e:
            raise _fail(e) from e
    return _LIBRARY


def _fail(e: WyltkmError) -> _Fail:
    if isinstance(e, (UnknownDesign, UnknownIcon)):
        return _Fail(str(e), EXIT_NOT_FOUND)
    if isinstance(e, DataError):
        return _Fail(f"broken data: {e}", EXIT_DATA)
    return _Fail(str(e), EXIT_INVALID)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="wyltkm")
def main():
    """WYLTKM – "Would you like to know more?" QR codes.

    Creates QR codes with a text on top, an icon in the middle and a "would
    you like to know more?" line at the bottom, in one of several designs.
    Output is SVG (all shapes are paths, usable for laser cutters) or PNG.

    \b
    Examples:
      wyltkm render https://example.org -t "Laser cutter" -o laser.svg
      wyltkm render https://example.org -d 38c3 -i fa:solid/bolt -o code.png
      wyltkm designs
    """


@main.command()
@click.argument("content")
@click.option("-t", "--text", "texts", multiple=True, metavar="TEXT",
              help="Top text. Repeat for several lines.")
@click.option("-d", "--design", help="Design name (see 'wyltkm designs'). "
              "Default: the configured default design.")
@click.option("-s", "--scheme", help="Colour scheme of the design, for designs that have "
              "schemes. Default: the design's default scheme.")
@click.option("-i", "--icon", help="Icon in the centre: source:name (e.g. fa:solid/cat), "
              "or 'none'. Default: the design's default icon. Find icons with "
              "'wyltkm icons search'.")
@click.option("--icon-file", type=click.File("rb"),
              help="SVG file to use as icon (not together with --icon).")
@click.option("-w", "--width", type=click.IntRange(MIN_WIDTH, MAX_WIDTH), default=DEFAULT_WIDTH,
              show_default=True, help="Width of the whole image in px.")
@click.option("--border/--no-border", default=None,
              help="Quiet zone of 4 modules around the image. Default: from the design.")
@click.option("--background/--transparent", default=None,
              help="With the design's background colour, or transparent. Default: from "
              "the design.")
@click.option("-f", "--format", "fmt", type=click.Choice(["svg", "png"]),
              help="Output format. Default: from the extension of --output, else svg.")
@click.option("-o", "--output", type=click.Path(dir_okay=False, allow_dash=True), default="-",
              show_default=True, help="Output file; '-' writes to stdout.")
@click.option("--licences", "show_licences", is_flag=True,
              help="Print the licences of all parts of the image to stderr.")
@click.option("--no-licence-metadata", is_flag=True,
              help="Leave the licence info out of the image file (SVG and PNG).")
def render(content, texts, design, scheme, icon, icon_file, width, border, background, fmt,
           output, show_licences, no_licence_metadata):
    """Render a QR code for CONTENT (usually a URL).

    Warnings (e.g. a missing font) go to stderr. When a part of the image
    requires attribution or has an unclear licence, a short note goes to
    stderr as well; --licences prints the full list.
    """
    if fmt is None:
        fmt = "png" if output != "-" and output.lower().endswith(".png") else "svg"
    try:
        icon_svg = icon_file.read() if icon_file is not None else None
        request = Request(content=content, text="\n".join(texts), design=design, scheme=scheme,
                          icon=icon, icon_svg=icon_svg, width=width, border=border, background=background,
                          licence_metadata=not no_licence_metadata)
        lib = _library()
        result = render_png(lib, request) if fmt == "png" else render_svg(lib, request)
    except WyltkmError as e:
        raise _fail(e) from e
    data = result.png if fmt == "png" else result.svg.encode("utf-8")
    if output == "-":
        sys.stdout.buffer.write(data)
        sys.stdout.flush()
    else:
        Path(output).write_bytes(data)
    for w in result.warnings:
        click.echo(f"warning: {w}", err=True)
    if show_licences:
        click.echo("Licences:", err=True)
        for lic in result.licences:
            click.echo(f"  {lic.text()}", err=True)
    elif result.licence_notes:
        click.echo("Licence notes (all licences: --licences):", err=True)
        for lic in result.licence_notes:
            click.echo(f"  {lic.text()}", err=True)


@main.group(invoke_without_command=True)
@click.pass_context
def designs(ctx):
    """List designs, or show one with 'designs show NAME'."""
    if ctx.invoked_subcommand is not None:
        return
    lib = _library()
    for name in lib.designs.names():
        try:
            d = lib.designs.get(name)
        except WyltkmError as e:
            click.echo(f"{name:16} BROKEN: {e}")
            continue
        mark = " (default)" if name == lib.default_design else ""
        schemes = f"  schemes: {', '.join(d.schemes)}" if d.schemes else ""
        click.echo(f"{name:16} {d.title}{mark}{schemes}")


@designs.command("show")
@click.argument("name")
@click.option("--preview", "preview_scheme", is_flag=False, flag_value="", default=None,
              metavar="[SCHEME]", help="Write a sample image of the design (and scheme) "
              "instead of showing its values; use with -o.")
@click.option("-o", "--output", type=click.Path(dir_okay=False, allow_dash=True), default="-",
              show_default=True, help="Output file for --preview; svg or png by extension.")
def designs_show(name, preview_scheme, output):
    """Show the resolved values of design NAME, or write a preview image."""
    lib = _library()
    try:
        d = lib.designs.get(name)
        if preview_scheme is not None:
            req = preview_request(name, preview_scheme or None, d.title)
            png = output != "-" and output.lower().endswith(".png")
            result = render_png(lib, req) if png else render_svg(lib, req)
            data = result.png if png else result.svg.encode("utf-8")
            if output == "-":
                sys.stdout.buffer.write(data)
                sys.stdout.flush()
            else:
                Path(output).write_bytes(data)
            for w in result.warnings:
                click.echo(f"warning: {w}", err=True)
            return
    except WyltkmError as e:
        raise _fail(e) from e
    click.echo(f"{d.name}: {d.title}")
    if d.description:
        click.echo(f"  {d.description}")
    click.echo(f"  directory: {d.dirs[0]}")
    if len(d.dirs) > 1:
        click.echo(f"  inherits from: {', '.join(p.name for p in d.dirs[1:])}")
    if d.schemes:
        click.echo(f"  schemes (default {d.default_scheme}):")
        for s in d.schemes.values():
            click.echo(f"    {s.name}: {s.title}")
            _colours(s.colours, "      ")
    else:
        click.echo("  colours:")
        _colours(d.base_colours, "    ")
    q = d.qr
    click.echo(f"  qr: modules {q.module_shape}, finder ring {q.finder_ring_shape}, "
               f"finder centre {q.finder_centre_shape}")
    click.echo("  fonts:")
    for role, fonts in (("top", d.top.fonts), ("bottom", d.bottom.style.fonts),
                        ("side", d.side.fonts)):
        if role == "bottom" and d.bottom.type != "text":
            continue
        _font_line(lib, role, fonts, d)
    if d.bottom.type == "text":
        lines = [''.join(f"[{r.text}]" if r.highlight else r.text for r in line)
                 for line in d.bottom.lines]
        click.echo(f"  bottom: {' / '.join(lines)}")
    elif d.bottom.type == "svg":
        click.echo(f"  bottom: graphic {d.bottom.svg}")
    click.echo(f"  defaults: icon {d.defaults.icon}, border {d.defaults.border}, "
               f"background {d.defaults.background}")
    click.echo(f"  licence: {d.licence.text()}")


def _colours(colours: dict[str, str], indent: str):
    bg = colours["background"]
    for k, v in colours.items():
        note = ""
        if k in ("modules", "finder_ring", "finder_centre"):
            ratio = contrast(v, bg)
            note = f"  contrast {ratio:.1f}" + (
                "  LOW, may not scan everywhere" if ratio < MIN_CONTRAST else "")
        click.echo(f"{indent}{k:14} {v}{note}")


def _font_line(lib: Library, role: str, fonts, d):
    if not fonts:
        click.echo(f"    {role:7} fallback font (none set)")
        return
    for name in fonts:
        path = lib.fonts.find(name, list(d.dirs))
        if path:
            click.echo(f"    {role:7} {name} -> {path}")
            return
    click.echo(f"    {role:7} {', '.join(fonts)} NOT FOUND, fallback font used")


@main.group(invoke_without_command=True)
@click.pass_context
def icons(ctx):
    """List icon sources; search, list and show icons.

    Icons are named source:name, e.g. fa:solid/cat or carbon:boot.
    """
    if ctx.invoked_subcommand is not None:
        return
    lib = _library()
    for src in lib.icons.sources():
        click.echo(f"{src.name:12} {src.title}: {len(src.files)} icons, "
                   f"licence {src.licence.name}")


@icons.command("list")
@click.argument("source")
@click.argument("folder", required=False)
def icons_list(source, folder):
    """List the icons of SOURCE, optionally only those in FOLDER (e.g. solid)."""
    lib = _library()
    try:
        src = lib.icons.source(source)
    except WyltkmError as e:
        raise _fail(e) from e
    prefix = folder.strip("/") + "/" if folder else ""
    for icon in src.names():
        if icon.startswith(prefix):
            label = src.info(icon).label
            click.echo(f"{src.name}:{icon}" + (f"  {label}" if label else ""))


@icons.command("search")
@click.argument("query", nargs=-1, required=True)
@click.option("-s", "--source", help="Only search this source.")
@click.option("-n", "--limit", default=30, show_default=True, help="Show at most this many "
              "hits; 0 for all.")
def icons_search(query, source, limit):
    """Search icons by name, label and search terms. All words must match;
    best matches first."""
    lib = _library()
    try:
        hits = lib.icons.search(" ".join(query), source, limit)
    except WyltkmError as e:
        raise _fail(e) from e
    for h in hits:
        click.echo(f"{h.name}" + (f"  {h.label}" if h.label else ""))
    if not hits:
        click.echo("no icons found", err=True)


@icons.command("show")
@click.argument("name")
@click.option("-c", "--colour", help="Colour (#rrggbb) for icons that are recoloured.")
@click.option("-o", "--output", type=click.Path(dir_okay=False, allow_dash=True), default="-",
              show_default=True, help="Output file; '-' writes to stdout.")
def icons_show(name, colour, output):
    """Write the normalised icon NAME as SVG, as it is placed in the code."""
    lib = _library()
    if colour is not None and not re.match(r"^#[0-9a-fA-F]{6}$", colour):
        raise _Fail("colour must be #rrggbb", EXIT_INVALID)
    try:
        svg = render_icon(lib, name, colour)
        src, icon = lib.icons.lookup(name)
    except WyltkmError as e:
        raise _fail(e) from e
    if output == "-":
        click.echo(svg, nl=False)
    else:
        Path(output).write_text(svg, encoding="utf-8")
    click.echo(f"licence: {src.licence.text()}", err=True)


@main.command()
def licences():
    """List the licences of all designs, icon sources and bundled fonts."""
    lib = _library()
    click.echo("Designs:")
    for name in lib.designs.names():
        try:
            click.echo(f"  {lib.designs.get(name).licence.text()}")
        except WyltkmError as e:
            click.echo(f"  {name}: BROKEN: {e}")
    click.echo("Icon sources:")
    for src in lib.icons.sources():
        click.echo(f"  {src.licence.text()}")
    click.echo("Bundled fonts:")
    for f in sorted(BUNDLED_DIR.iterdir()):
        if f.suffix.lower() in (".ttf", ".otf"):
            click.echo(f"  {licmod.for_font(f).text()}")
    click.echo(f"  {FALLBACK_LICENCE.text()}")


@main.command("config")
def config_cmd():
    """Show the config file and the data directories in use."""
    lib = _library()
    cfg = lib.config
    click.echo(f"config file:    {cfg.path or 'none (defaults)'}")
    click.echo(f"default design: {cfg.default_design}")
    click.echo(f"system fonts:   {'on' if cfg.system_fonts else 'off'}")
    click.echo("data directories (in search order):")
    used = set(cfg.data_dirs)
    for d in cfg.candidates:
        state = "used" if d.path in used else ("duplicate" if d.exists else "missing")
        click.echo(f"  {d.path}  [{d.origin}, {state}]")
    click.echo(f"  {BUNDLED_DIR.parent}  [package, used]")
    w = cfg.web
    click.echo(f"web: max_width {w.max_width}, max_upload_bytes {w.max_upload_bytes}, "
               f"max_upload_elements {w.max_upload_elements}, "
               f"max_upload_depth {w.max_upload_depth}")


@main.command()
def fonts():
    """Show available fonts, and the fonts each design needs and where they
    are found."""
    lib = _library()
    click.echo("Fonts in font directories:")
    for name, path in lib.fonts.available().items():
        click.echo(f"  {name}  {path}  ({licmod.for_font(path).name})")
    click.echo(f"System fonts: {'searched' if lib.fonts.system_fonts else 'not searched'}")
    click.echo("Fonts of the designs:")
    for name in lib.designs.names():
        try:
            d = lib.designs.get(name)
        except WyltkmError as e:
            click.echo(f"  {name}: BROKEN: {e}")
            continue
        click.echo(f"  {name}:")
        for role, fonts_ in (("top", d.top.fonts), ("bottom", d.bottom.style.fonts),
                             ("side", d.side.fonts)):
            if role == "bottom" and d.bottom.type != "text":
                continue
            _font_line(lib, role, fonts_, d)


@main.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=5000, show_default=True, type=int)
@click.option("--debug", is_flag=True, help="Flask debug mode (reloads on changes).")
def web(host, port, debug):
    """Start the web app with Flask's development server.

    Needs the web extra (pip install 'wyltkm[web]'). For hosting, use a WSGI
    server with 'wyltkm.web:create_app()'.
    """
    try:
        from wyltkm.web import create_app
    except ImportError as e:
        raise click.ClickException(
            f"the web extra is not installed ({e}); install 'wyltkm[web]'") from e
    create_app().run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    sys.exit(main())
