# Would you like to know more?

WYLTKM creates QR codes in a fixed layout: a text on top, a styled QR code
with an optional icon in its centre, and a "would you like to know more?" line
at the bottom. It was created for the maker space [Attraktor e.V.][attraktor],
to make it easy to create QR codes that supply additional information about
projects and workshops, and also does designs for the Chaos Communication
Congress.

The SVG output consists of filled paths only, so it works for laser cutters
and plotters as well as for print.

The project has three parts that share one engine:

- `wyltkm.core`: a Python library that turns a request into an SVG or PNG.
- `wyltkm`: a command line tool.
- `wyltkm.web`: a [Flask][flask] app with a form and preview, which can be
  hosted.

## Install

```sh
pip install wyltkm            # library and command line tool
pip install 'wyltkm[web]'     # with the web app
```

For development, with [uv](https://docs.astral.sh/uv/):

```sh
uv sync --extra web
uv run pytest
uv run wyltkm web --debug
```

## Use

```sh
wyltkm render https://wiki.attraktor.org/Laser -t "Laser cutter" -o laser.svg
wyltkm render https://events.ccc.de -d 38c3 -i fa:solid/bolt -o code.png
wyltkm designs
wyltkm --help
```

Hosting the web app: `gunicorn 'wyltkm.web:create_app()'`.

## Fonts and licences

Free fonts (Hack, Jersey 10, Pilowlava, Space Grotesk) ship with the package.
The Attraktor design uses Agency FB, which is not free: install it as a
system font or in a font directory of the install. Without it, a fallback
font is used and a warning is shown.

Every image is made of parts with their own licences (design, icon, fonts).
CLI and web show them for each image, and by default the image file contains
them as well. `wyltkm licences` lists all of them.

## Documentation

See [docs/](docs/): architecture, rendering, designs, icons, licences,
configuration, CLI and web, and the development plans.

[attraktor]: https://www.attraktor.org
[flask]: https://flask.palletsprojects.com
