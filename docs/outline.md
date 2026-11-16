# WYLTKM – Concept and architecture

Nov 16, 2026 · @kratenko

## Overview and goals

WYLTKM is three things that share one engine:

- **Core** (`wyltkm.core`): a Python library that turns a request (content,
  text, design, icon, size options) into an SVG or PNG image. It knows
  designs, icon sources and fonts. It has no web or CLI code.
- **CLI** (`wyltkm`): a command line tool that creates the same images from
  the shell and lists designs, icons and fonts.
- **Web** (`wyltkm.web`): a Flask app with a form, live preview and download,
  that can be hosted.

Goals of the rewrite:

- A clean split: CLI and web only use the public core API, and can produce
  exactly the same images for the same request.
- Designs as data files, so new designs (40c3 and later) need no code. No
  design is special to the program; the default design is a setting
  (`attraktor` out of the box).
- SVG output whose QR code consists of paths only, usable for laser cutters
  and plotters.
- All free Font Awesome icons, plus Carbon, 40c3 assets, local directories and
  uploaded icons, all reachable from CLI and web.
- A defined place where installations put fonts; system fonts usable.
- A web interface that is easy to use and looks good.
- Accessibility: optionally, the content of the QR code as readable text
  along the image's right side, for people without a scanner.
- Licence conditions of every generated image are visible, in web and CLI
  ([licences.md](licences.md)).

## Decisions

| Topic | Decision |
| --- | --- |
| Rendering | Own SVG composition (QR from the module matrix, text via ziafont, icons as nested groups). PNG via cairosvg. reportlab and svglib are dropped. |
| QR elements | Paths only: modules, finder patterns, text glyphs and icons. No `rect`, `circle`, `use` or strokes. Strokes, clip paths or gradients inside an icon are kept and reported as "not laser-friendly". |
| Designs | TOML files, one directory per design, with inheritance and optional colour schemes. Built-ins ship in the package; installs can add or override designs. |
| Side text | Opt-in per image by the user; design gives default font, colour, direction and minimum size; long content wraps into columns. |
| Licences | Every part (icon source, design assets, fonts) carries licence data. Each render result lists the licences of the parts it used; web and CLI show them. The image file embeds them as metadata unless the request opts out. |
| Icons | Named `source:name`. Sources are zips or directories, configurable. Font Awesome is read from its release zip directly. |
| Fonts | Free (OFL and similar) design fonts are bundled. Others go into a font directory of the install. System fonts are searched too, unless switched off. Fonts are referred to by file name. |
| CLI | click, with help texts for every command and option. |
| Web forms | No WTForms or flask-wtf: the web app maps parameters to the core `Request`, which validates; there is no state to protect with CSRF tokens. |
| Version | The rewrite is released as 0.3.0. |
| Compatibility | Clean break: new URL parameters and icon names, no layer for old links. |
| Web UI | Server-rendered Flask templates, small vanilla JS for live preview and icon search. No npm, no build step. |
| Packaging | `pyproject.toml` (hatchling), `uv.lock`, Python ≥ 3.12, `src/` layout. Web dependencies are the optional extra `wyltkm[web]`. |
| Tests | pytest; golden-file tests for rendered SVGs, run with bundled fonts only and system fonts off, so they give the same result everywhere. |
| Asset zips | The Font Awesome zip, the 40c3 style guide zip and the Carbon icon zip are committed and packaged as they are. |
| Error correction | Always level H; not configurable. |

## Architecture

```
            ┌──────────────┐        ┌──────────────┐
  shell ──▶ │  wyltkm.cli  │        │  wyltkm.web  │ ◀── browser
            └──────┬───────┘        └──────┬───────┘
                   │   Request             │
                   ▼                       ▼
            ┌────────────────────────────────────┐
            │            wyltkm.core             │
            │  Library ─┬─ designs  (TOML)       │
            │           ├─ icons    (sources)    │
            │           └─ fonts    (lookup)     │
            │  render(request) ─▶ SVG ─▶ PNG     │
            └────────────────────────────────────┘
                   ▲
                   │ Config (config file, data dirs, env)
```

- `Config` is read once: config file, data directories, environment
  ([configuration.md](configuration.md)).
- `Library` is built from the config and holds the design registry, the icon
  sources and the font resolver. It is created once per process (the web app
  keeps one).
- `Request` is a plain value: content, text, design name, colour scheme,
  icon name or uploaded icon, width, border, background, side text on or off
  and its font, licence metadata on or off. Fields left empty (`None`) mean
  "default": from the config (design) or from the design (scheme, icon,
  border, background, side font). Creating a `Request` checks everything
  that needs no library: syntax of names, width range, content length.
  `render_*` then checks what needs the library: that design, scheme, icon
  and font exist. Both kinds of check live in the core, so CLI and web share
  them.
- `render_svg(library, request)` and `render_png(library, request)` are the
  entry points. They return a result with the image, warnings, and the
  licences of the parts used. Everything else in `wyltkm.core` is internal.

## Package layout

```
pyproject.toml
uv.lock
src/wyltkm/
  core/
    __init__.py        public API: Library, Request, render_svg, render_png, errors
    config.py          config file, data dirs, env
    request.py         Request and validation
    render.py          layout and SVG assembly
    qr.py              QR matrix and path generation
    text.py            text to paths (ziafont)
    svg.py             SVG parsing, sanitising, primitive-to-path conversion, recolouring
    designs.py         design loading, inheritance, registry
    icons/             icon source types (zip, dir), registry, search
    fonts.py           font resolution
    licences.py        licence records and collection per render
    data/
      designs/<name>/design.toml (+ assets)
      icons/           fontawesome-free-7.3.1-web.zip, 40c3 zip, carbon, attraktor
      fonts/           bundled free fonts with licence files
  cli/
    __init__.py        entry point `wyltkm` (click)
  web/
    __init__.py        create_app()
    templates/, static/
tests/
docs/
```

Rule: `wyltkm.core` imports neither `wyltkm.cli` nor `wyltkm.web`. The CLI
works without the web extra installed.

## Out of scope for now

- Other layouts than top text, QR, bottom line (e.g. side-by-side).
- Accounts, saved codes, a gallery.
- Data other than text and URLs (vCard or Wi-Fi helpers).
- Batch rendering from CSV (might come to the CLI later).
