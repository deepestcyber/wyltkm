# Icons

The icon sits in the centre of the QR code. Icons come from sources; each
icon has a name of the form `source:name`.

## Icon names

| Example | Source |
| --- | --- |
| `fa:solid/cat`, `fa:regular/heart`, `fa:brands/github` | Font Awesome Free |
| `carbon:boot` | IBM Carbon icons |
| `40c3:logos/40c3-logo-a`, `40c3:icons-deco/icon-cat`, `40c3:citizens/blahaj` | 40c3 style guide assets |
| `attraktor:logo`, `attraktor:logo-mono` | Attraktor logos |
| `<source>:<name>` | Sources configured by the install |

Names contain only `a-z`, `0-9`, `-` and `/` (for styles or folders). They
are validated before any file access, so no name can leave its source.

File names are turned into icon names by a fixed rule: path below the
source's prefix, extension `.svg` removed, lower-cased, `_` and spaces
replaced by `-`. A source may add a `rename` table for nicer names (e.g.
`"attraktor" = "logo"`). Files whose name does not fit after that, or whose
name is already taken by another file (Carbon has `3D-Cursor` and
`3D-cursor`), are skipped and logged at startup.

The request may also carry an uploaded icon instead of a name (see below), or
`none` for no icon. Without either, the design's default icon is used.

## Source types

| Type | Reads | Notes |
| --- | --- | --- |
| `zip` | SVG files inside a zip, below a prefix | Index built once at startup |
| `dir` | SVG files in a directory tree | |

A source is defined by a small TOML file:

```toml
# icons/fa.toml
name = "fa"
title = "Font Awesome Free 7.3.1"
type = "zip"
path = "fontawesome-free-7.3.1-web.zip"   # relative to this file
prefix = "fontawesome-free-7.3.1-web/svgs/"   # only files below it; names relative to it
include = []                               # optional: only these folders below prefix
recolour = true                            # fill all shapes with the design's icon colour
recolour_except = []                       # icon names, or folders ending in "/", where
                                           # recolour is the other way round
metadata = "fontawesome"                   # optional, zip only: "fontawesome" or "carbon"

[licence]                                  # see licences.md
name = "CC-BY-4.0"
url = "https://fontawesome.com/license/free"
holder = "Fonticons, Inc."
attribution = "Icon from Font Awesome Free, https://fontawesome.com, CC BY 4.0"
requires_attribution = true
```

A source may also have no licence record; it is then reported as "licence
unknown" with every image that uses it. Uploaded icons are reported as
"uploaded by the user".

Built-in sources live in the package (`wyltkm/core/data/icons/`). Installs
add sources by putting such a file (and its zip or directory) into `icons/`
of a data directory ([configuration.md](configuration.md)). A source with the
name of a built-in one replaces it.

### Built-in sources

| Name | Content | Licence |
| --- | --- | --- |
| `fa` | All of Font Awesome Free (solid, regular, brands), read from its release zip. Labels and search terms come from `metadata/icons.json` inside the zip. | Icons CC BY 4.0 |
| `carbon` | All IBM Carbon icons (32 px set), from the npm package `@carbon/icons`, repacked into a zip with labels and aliases | Apache 2.0 |
| `40c3` | Deco icons (`icons-deco/`), citizens (`citizens/`) and logos (`logos/`) from the 40c3 style guide zip. The logos are one colour each and take the design's icon colour; deco icons and citizens keep their colours. | CC0 |
| `attraktor` | Attraktor logo, colour and mono | unclear, holder Attraktor e.V. |

### Updating

- Font Awesome: download the "Free for Web" zip of a new version, put it into
  `src/wyltkm/core/data/icons/`, and change `path`, `prefix` and `title` in
  `fa.toml`. Remove the old zip. Icon names are those of the new version.
- Carbon: `python tools/update_carbon_icons.py VERSION` downloads that
  version of `@carbon/icons` and writes `carbon-icons-VERSION.zip`; then
  change `path` and `title` in `carbon.toml` and remove the old zip.
- 40c3: replace the style guide zip; names follow the file names.

Then run the tests: golden files that use a changed icon must be rewritten
(`UPDATE_GOLDEN=1 pytest`) after checking the new images.

## Colouring

With `recolour = true`, every visible shape of the icon gets the design's
icon colour and other fill and stroke settings are removed. Shapes that are
invisible (`fill="none"` without a stroke, e.g. the bounding box in every
Carbon icon) stay invisible. With `recolour = false`, the
icon keeps its own colours (e.g. the colour Attraktor logo, 40c3 citizens).

## Normalising

Every icon goes through the same steps before it is placed:

1. Parse with a safe XML parser (no entities, no external resources).
2. Drop everything but shapes, groups, clip paths and gradients: no scripts,
   `foreignObject`, images, links. Styles from `<style>` blocks and `style`
   attributes are resolved into attributes (the 40c3 and Carbon files use
   classes).
3. Convert primitives to paths ([rendering.md](rendering.md)).
4. Recolour if the source says so.
5. Scale into the empty centre square, keeping the aspect ratio.

### Strokes, clip paths and gradients

Some SVG features draw correctly in a browser or PNG, but are not plain
filled paths:

- **Strokes**: a line drawn with a width along a path. A laser cutter or
  plotter usually sees only the centre line and ignores the width; an engrave
  job does not fill it.
- **Clip paths**: a shape that cuts away parts of another. Laser cutter
  software often ignores clipping and shows the uncut shape.
- **Gradients**: no single fill colour.

The built-in sources hardly use these: Font Awesome and Carbon icons are
filled paths only; two 40c3 assets use a clip path. Strokes would mostly come
from uploads and local sources.

What we do: the image is drawn correctly in every case, and the result
carries a warning "not laser-friendly: <reason>", shown in CLI and web.
Turning strokes into outlines and applying clip paths geometrically (with a
path geometry library) is possible later if needed; it is not part of the
plans now.

## Uploaded icons

- CLI: `--icon-file path/to/icon.svg`.
- Web: file upload in the form field `icon_file`. The file goes through the
  same normalising, with limits from the config: size (`max_upload_bytes`,
  default 256 KiB), number of elements (`max_upload_elements`, default
  5000) and nesting depth (`max_upload_depth`, default 20).
- A request has either an icon name or an uploaded icon, never both; CLI and
  web reject the combination.
- Uploaded icons are not stored on the server. A link to a rendered image
  cannot carry an uploaded icon; the web page renders it from the form data.

## Search

The CLI (`wyltkm icons search cat`) and the web app (`/api/icons?q=cat`, and
the search field of the form) search icons by name, and for sources with
metadata (Font Awesome, Carbon) by label and search terms. All words of the
query must match. Best matches first: the name is the word, the name starts
with the word, the name contains it, the label contains it, a search term
starts with it.

Normalised icons are cached per process (256 icon and colour pairs). Zip
files stay open once read.

Sources with metadata (Font Awesome, Carbon) only offer icons their metadata
knows. Font Awesome's zip also holds alias files under older names (e.g.
`arrow-alt-circle-up`); leaving them out avoids every such icon appearing
twice when browsing. Icons are grouped in folders by the first part of their
name (`fa:solid/...`, `40c3:citizens/...`); the browser in the web app lists
them per source and folder.

SVG features handled when normalising include `<switch>` (only its first
usable child is drawn; ten Carbon icons use it).
