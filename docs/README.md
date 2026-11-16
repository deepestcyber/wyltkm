# WYLTKM documentation

WYLTKM ("Would you like to know more?") creates QR codes in a fixed layout: a
text line on top, a styled QR code with an optional icon in its centre, and a
"would you like to know more?" line at the bottom. It was made for the maker
space [Attraktor e.V.](https://www.attraktor.org) and also does designs for
the Chaos Communication Congress.

These documents describe the target state of the rewrite that started in
November 2026. Until the plans in [development/](development/) are
completed, parts of them are not built yet; the plans say what is done.

| Document | Content |
| --- | --- |
| [outline.md](outline.md) | Goals, decisions, architecture and package layout |
| [rendering.md](rendering.md) | How an image is built: layout, QR shapes, paths only, output formats |
| [designs.md](designs.md) | Design files: format, inheritance, built-in designs |
| [icons.md](icons.md) | Icon sources, icon names, colouring, uploads, licences |
| [licences.md](licences.md) | Licence records, and how web and CLI show them per image |
| [configuration.md](configuration.md) | Config file, data directories, font lookup |
| [cli.md](cli.md) | The `wyltkm` command line tool |
| [web.md](web.md) | The Flask web app and its HTTP interface, deployment |
| [development/](development/) | Plans we work along (we have no ticket system) |
