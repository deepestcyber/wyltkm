# Command line tool

`wyltkm` is installed as a console script with the package. It is built with
[click](https://click.palletsprojects.com): every command and option has a
help text (`wyltkm --help`, `wyltkm render --help`), and the help is the
reference; this page gives the overview. It uses the same core and
configuration as the web app, so the same options give the same image.

## Rendering

```sh
wyltkm render https://wiki.attraktor.org/Laser \
  --text "Laser cutter" \
  --design attraktor \
  --icon fa:solid/bolt \
  -o laser.svg
```

| Option | Meaning |
| --- | --- |
| `CONTENT` | Data in the QR code, usually a URL (positional) |
| `-t`, `--text` | Top text; several `--text` give several lines; `[...]` in the highlight colour, `[[`/`]]` for a bracket |
| `-b`, `--bottom` | Own bottom line instead of the design's, e.g. `"SCAN [ME]"`; several give several lines |
| `--no-bottom` | No bottom line at all |
| `--top-justify` / `--top-center` | Justify the top text lines to full width, or centre them (default from the design: justified) |
| `--bottom-justify` / `--bottom-center` | The same for the bottom line |
| `-d`, `--design` | Design name (default from config, else `attraktor`) |
| `-s`, `--scheme` | Colour scheme of the design (default: its main colours) |
| `-i`, `--icon` | Icon name `source:name`, or `none` |
| `--icon-file` | SVG file to use as icon; not together with `--icon` |
| `-w`, `--width` | Image width in px (default 250, 50 to 10000) |
| `--border` / `--no-border` | Quiet zone of 4 modules (default from design) |
| `--background` / `--transparent` | With or without background (default from design) |
| `--side-text` / `--no-side-text` | Readable content text along the right side (default off) |
| `--side-font` | Font file name for the side text (default from design) |
| `-f`, `--format` | `svg` or `png`; default from the extension of `-o`, else `svg` |
| `-o`, `--output` | Output file; `-` for stdout (the default) |
| `--licences` | Print the licences of all parts used to stderr |
| `--no-licence-metadata` | Leave the licence info out of the image file (SVG and PNG) |

Warnings (missing font, not laser-friendly icon) and, when a part requires
attribution or its licence is unclear or unknown, a short licence note go to
stderr.

Exit codes: 0 success, 1 invalid request (e.g. unknown scheme), 2 wrong
command line usage, 3 unknown design or icon, 4 broken data (a design or
icon source of the install is faulty).

## Inspecting

```sh
wyltkm designs                 # list designs and their schemes
wyltkm designs show 40c3       # resolved values, fonts found, contrast
wyltkm designs show 40c3 --preview pink -o p.png   # sample image of a scheme
wyltkm icons                   # list sources
wyltkm icons list fa           # list icons of a source
wyltkm icons search cat        # search all sources
wyltkm icons show fa:solid/cat -o cat.svg   # the normalised icon
wyltkm fonts                   # fonts available, and those the designs need and where they resolve
wyltkm licences                # licences of all sources, designs and fonts
wyltkm config                  # config file and data directories in use
```

## Web server for development

With the web extra installed, `wyltkm web` starts the Flask development
server. For hosting see [web.md](web.md).
