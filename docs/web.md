# Web app

`wyltkm.web` is a Flask app around the core. It needs the extra:
`pip install wyltkm[web]` (or `uv sync --extra web`).

## Interface

One page:

- Form on one side: content, top text, design (with small previews), colour
  scheme (shown only when the design has schemes), icon picker with search
  (name and Font Awesome search terms, filter by source), icon upload, width,
  border, background, readable side text (checkbox, with a font selection
  shown when it is on), licence info in the file (checkbox, on by default).
- Preview on the other side, updated live while typing (debounced), with
  download buttons for SVG and PNG and a link to the current settings.
- Warnings from the core (missing font, not laser-friendly icon) shown next
  to the preview.
- Licence box under the preview: licences of the parts in the current image,
  attribution text ready to copy ([licences.md](licences.md)).
- Footer: version, source link, link to the licences page.

Form handling has no WTForms or flask-wtf: parameters are read into the core
`Request`, which validates them for CLI and web alike, and errors are shown
next to the fields. There are no sessions or accounts, so no CSRF tokens.

It works without JavaScript as a plain form with a preview button. JavaScript
is small vanilla code shipped as a static file: no npm, no build step.

Layout and visual design are worked out in the web plan.

## HTTP interface

| Route | Method | Result |
| --- | --- | --- |
| `/` | GET | The page; form values from the query parameters |
| `/render.svg`, `/render.png` | GET | Image for the query parameters |
| `/render.svg`, `/render.png` | POST | Image for form data (`multipart/form-data`), same fields, plus an uploaded icon in `icon_file` |
| `/api/fonts` | GET | Fonts users can pick for the side text, as JSON |
| `/api/designs` | GET | Designs as JSON (name, title, description, colours, schemes, licence, preview URLs) |
| `/designs/<name>/preview.svg?scheme=` | GET | Preview of a design (sample content, rendered on request, cached) |
| `/api/licences?<render parameters>` | GET | Licences of the parts an image with these parameters uses, as JSON |
| `/licences` | GET | Licences of all sources, designs and fonts |
| `/api/icons?q=&source=&limit=` | GET | Icon search as JSON |
| `/icons/<source>/<name>.svg` | GET | Normalised icon, recoloured with `?colour=` |
| `/help` | GET | Help page |

Query parameters of `/render.*` and `/`:

| Parameter | Meaning |
| --- | --- |
| `content` | Data in the QR code |
| `text` | Top text; line breaks (`\n`, `%0A` in URLs) separate lines |
| `design` | Design name |
| `scheme` | Colour scheme of the design |
| `icon` | Icon name or `none` |
| `width` | Image width in px |
| `border` | `1` or `0` |
| `background` | `1` or `0` (`0`: transparent); default from design |
| `side` | `1`: readable side text |
| `side_font` | Font file name for the side text |
| `licence_metadata` | `0`: no licence info in the image file (default `1`) |
| `download` | `1`: send as attachment; file name from the slugified top text (all lines), else `wyltkm-qr` |

Invalid parameters give `400` with a short message, including an unknown
scheme or side font. Unknown designs or icons give `404`.

## Limits

From the `[web]` table of the config file: maximum width, and size, element
and depth limits for uploads. The content length is limited by what a QR code can hold at the chosen
error correction.

## Deployment

The app is a WSGI app: `wyltkm.web:create_app()`. It reads the configuration
like the CLI (config file, data directories, environment) once at start. Run it with any WSGI
server, e.g.:

```sh
gunicorn 'wyltkm.web:create_app()' --bind 0.0.0.0:8000
```

Set `WYLTKM_CONFIG` to the config file of the install and put fonts and extra
designs or icon sources into a data directory (see
[configuration.md](configuration.md)). The app keeps no state; it can run in
several processes.
