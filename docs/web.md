# Web app

`wyltkm.web` is a Flask app around the core. It needs the extra:
`pip install wyltkm[web]` (or `uv sync --extra web`).

## Interface

One page, two columns (on phones the preview comes first):

- **Form** in cards: link or text in the code, top text (with `[...]` for
  the highlight colour), bottom line (design, own text or none), each text
  justified or centred; design as small
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
  `/browse` (paged, server-rendered); picking an icon there leads back
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
| `/browse?q=&source=&folder=&offset=&<form parameters>` | GET | The icon browser as a page; links lead back to `/` with the form parameters and the picked icon |
| `/icon/<source>/<name>.svg` | GET | Normalised icon, recoloured with `?colour=` |
| `/help` | GET | Help page |

Query parameters of `/render.*` and `/`:

| Parameter | Meaning |
| --- | --- |
| `content` | Data in the QR code |
| `text` | Top text; line breaks (`\n`, `%0A` in URLs) separate lines; `[...]` in the highlight colour |
| `bottom_mode` | Bottom line: empty or `design` (the design's), `text` (own text from `bottom`), `none` |
| `bottom` | Own bottom text, used with `bottom_mode=text`; lines and `[...]` as for `text` |
| `top_justify`, `bottom_justify` | `0`: centre the lines of that text; `1` or empty: justified (the default) |
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

The app must be served at the root of its host (its own vhost), not below a
path: the page and its JavaScript use absolute paths like `/render.svg`.

No route of the app starts with `/icons/`: Debian and Ubuntu Apache map
`/icons/` to its own directory server-wide (`Alias /icons/` in
`mods-enabled/alias.conf`), before any `.htaccess` rewrite. Icon images are
therefore served at `/icon/...` and the icon browser page at `/browse`.

Two ways are described: a WSGI server behind a reverse proxy, for a server you
control, and FastCGI under Apache, for shared hosting.

### WSGI server behind a reverse proxy

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

### Apache with FastCGI (shared hosting)

For a host where you have a shell but no root, the system's Python is too old,
and Apache runs the app through FastCGI with rewrites in `.htaccess`. Paths
below use `/srv/wyltkm`; any directory outside the document root that the
FastCGI process can read works.

1. **Python.** Install [uv](https://docs.astral.sh/uv/), a single program in
   your home directory, and let it put a prebuilt Python into the project
   directory. No root and no compiler are needed; the host needs outbound
   HTTPS and glibc 2.17 or newer (`ldd --version`):

   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   export UV_PYTHON_INSTALL_DIR=/srv/wyltkm/python
   uv python install 3.12
   ```

2. **Environment and package.** Create a venv with that Python and install
   WYLTKM with the web extra and `flup` (the FastCGI server):

   ```sh
   uv venv --python 3.12 /srv/wyltkm/venv
   uv pip install --python /srv/wyltkm/venv/bin/python 'wyltkm[web]' flup
   ```

   Install from a git URL (`'wyltkm[web] @ git+https://github.com/deepestcyber/wyltkm'`)
   or, without git on the host, from a wheel built elsewhere with `uv build`
   (`'/path/wyltkm-<version>-py3-none-any.whl[web]'`). CairoSVG needs the
   system's cairo library.

3. **Config and fonts.** Write `/srv/wyltkm/config.toml` from
   [examples/config.toml](examples/config.toml) with
   `data_dirs = ["/srv/wyltkm"]` and `system_fonts = false`, and put fonts the
   package does not bundle into `/srv/wyltkm/fonts/`, e.g. `AgencyFB-Bold.ttf`
   for the Attraktor design (optionally with `AgencyFB-Bold.ttf.licence.toml`).
   Check with:

   ```sh
   export WYLTKM_CONFIG=/srv/wyltkm/config.toml
   /srv/wyltkm/venv/bin/wyltkm config
   /srv/wyltkm/venv/bin/wyltkm fonts
   /srv/wyltkm/venv/bin/wyltkm render https://example.org -o /tmp/test.png
   ```

4. **FastCGI script and rewrites.** Put
   [examples/qr.fcgi](examples/qr.fcgi) (executable, shebang pointing to the
   venv's Python) and [examples/htaccess](examples/htaccess) (as `.htaccess`)
   into the document root of the vhost. The script sets `WYLTKM_CONFIG`
   itself, since with mod_fcgid a `SetEnv` in `.htaccess` often does not reach
   the process. Do not keep a directory named `static` in the document root;
   it would catch requests meant for the app.

5. **Switch and restart.** FastCGI processes keep running; a changed
   `qr.fcgi` usually makes mod_fcgid start new ones, otherwise restart them
   the way the host allows. Each process loads the icon index and fonts once.

Updating:

- WYLTKM: run the `uv pip install` command again, with
  `--reinstall-package wyltkm`.
- Python: `uv python install 3.13`, create a new venv, install into it,
  change the shebang of `qr.fcgi`, then remove the old venv and Python. Until
  then, changing the shebang back is the way back. The venv depends on the
  Python it was made with, so do not remove that Python while the venv is in
  use.
- If FastCGI runs as another user than yours (no suEXEC), that user must be
  able to read `/srv/wyltkm/python` and the venv.
