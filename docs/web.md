# Web app

`wyltkm.web` is a Flask app around the core. It needs the extra:
`pip install wyltkm[web]` (or `uv sync --extra web`).

## Interface

One page, two columns (on phones the preview comes first):

- **Form** in cards: link or text in the code and top text; design as small
  previews, with the design's schemes below as chips (colour dot and name); icon
  search over all sources with a source filter and a grid of hits drawn in
  the design's colours, "Design" and "None" choices, a "Browse" button for
  the icon browser, and an upload for an own SVG; options as segmented buttons (background, border, side text with
  a font field, width, licence info in the file).
- **Preview**: the image lies on a cutting mat with a module-like grid,
  framed by crop marks, with its size and number of modules underneath. It
  follows every change after a short pause; the address bar keeps the
  current settings, so the page can be bookmarked or shared ("Copy link").
- **Download SVG** (main action) and **Download PNG**, file name from the top
  text. With an uploaded icon, the downloads post the form instead.
- Warnings from the core (missing font, not laser-friendly icon) and the
  licences of the parts of the current image, with the attribution text
  ready to copy ([licences.md](licences.md)), below the preview.
- **Icon browser**: a dialog in the page (the native `<dialog>`: Escape
  closes it, focus stays inside) with all icons. Search field, sources as
  chips with their number of icons, folders of the chosen source on the left
  (e.g. solid, regular, brands), a grid that loads more icons while
  scrolling, and a bar with the chosen icon's name, label, source and
  licence. Click picks, double-click or Enter uses it, arrow keys move.
  Without JavaScript, "Browse" opens the same view as the page
  `/icons/browse` (paged, server-rendered); picking an icon there leads back
  to the form with all settings. Icon tiles show the design's background and
  icon colour, so each icon looks as it will in the code.
- Header with Help, Licences and a theme switch (system, dark, light;
  remembered in the browser); footer with version, source and licences.

Look: quiet graphite surfaces in dark and light, one accent (the blue of the
Attraktor favicon), Space Grotesk for the interface and Hack for figures. The
colour of the page comes from the code in the preview.

Form handling has no WTForms or flask-wtf: parameters are read into the core
`Request`, which validates them for CLI and web alike. There are no sessions
or accounts, so no CSRF tokens.

Without JavaScript the page is a plain form: "Update preview" and the icon
search button send it, and everything but the upload works. The JavaScript
is one small vanilla file (`static/app.js`): no npm, no build step.

## HTTP interface

| Route | Method | Result |
| --- | --- | --- |
| `/` | GET | The page; form values from the query parameters |
| `/render.svg`, `/render.png` | GET | Image for the query parameters |
| `/render.svg`, `/render.png` | POST | Image for form data (`multipart/form-data`), same fields, plus an uploaded icon in `icon_file` |
| `/api/fonts` | GET | Fonts users can pick for the side text, as JSON |
| `/api/designs` | GET | Designs as JSON (name, title, description, colours, schemes, licence, preview URLs) |
| `/designs/<name>/preview.svg?scheme=` | GET | Preview of a design (sample content, rendered on request, cached) |
| `/api/render-info?<render parameters>` | GET, POST | Size, number of modules, warnings and licences of the image, as JSON (POST with an uploaded icon) |
| `/ui-fonts/<file>` | GET | The two fonts of the page itself |
| `/api/licences?<render parameters>` | GET | Licences of the parts an image with these parameters uses, as JSON |
| `/licences` | GET | Licences of all sources, designs and fonts |
| `/api/icons?q=&source=&limit=` | GET | Icon search as JSON (name, label, URL) |
| `/api/icon-sources` | GET | Icon sources as JSON (name, title, number of icons, folders with counts, licence) |
| `/api/icons/browse?q=&source=&folder=&offset=&limit=` | GET | All matching icons a page at a time (default 120), with the total; an empty `q` lists all |
| `/icons/browse?q=&source=&folder=&offset=&<form parameters>` | GET | The icon browser as a page; links lead back to `/` with the form parameters and the picked icon |
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
like the CLI (config file, data directories, environment) once at start, and
keeps no state, so it can run in several processes.

1. Install it in its own environment, with a WSGI server:
   `python -m venv /opt/wyltkm && /opt/wyltkm/bin/pip install 'wyltkm[web]' gunicorn`.
2. Write the config file, e.g. `/etc/wyltkm/config.toml`, starting from
   [examples/config.toml](examples/config.toml). For a server, set
   `system_fonts = false` and put every font the designs need into `fonts/`
   of a data directory, with a licence record next to each
   ([configuration.md](configuration.md)). `wyltkm config` and `wyltkm fonts`
   (with `WYLTKM_CONFIG` set) show what the app will use.
3. Run it, e.g. with the systemd unit in
   [examples/wyltkm.service](examples/wyltkm.service):
   `gunicorn --workers 3 --bind 127.0.0.1:8000 'wyltkm.web:create_app()'`,
   with `WYLTKM_CONFIG` pointing to the config file.
4. Put a reverse proxy (nginx, Caddy) in front for TLS. Rendered images,
   previews and icons carry `ETag` and `Cache-Control` headers, so the proxy
   or browsers can cache them.

The page loads no external resources: its fonts (Space Grotesk, Hack) are
served from the package at `/ui-fonts/`.
