# Icons

The icon sits in the centre of the QR code. Icons come from sources; each
icon has a name of the form `source:name`.

## Icon names

| Example | Source |
| --- | --- |
| `fa:solid/cat`, `fa:regular/heart`, `fa:brands/github` | Font Awesome Free |
| `carbon:boot` | IBM Carbon icons |
| `40c3:icon-cat`, `40c3:citizen-blahaj` | 40c3 style guide assets |
| `attraktor:logo`, `attraktor:logo-mono` | Attraktor logos |
| `<source>:<name>` | Sources configured by the install |

Names contain only `a-z`, `0-9`, `-` and `/` (for styles or folders). They
are validated before any file access, so no name can leave its source.

The request may also carry an uploaded icon instead of a name (see below), or
`none`. Without an icon, the design's default icon is used.

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
prefix = "fontawesome-free-7.3.1-web/svgs/"
recolour = true                            # fill all shapes with the design's icon colour
metadata = "fontawesome"                   # optional: reader for labels and search terms

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
| `fa` | All of Font Awesome Free, read from its release zip. Updating means replacing the zip and the version in `fa.toml`. Labels and search terms come from `metadata/icons.json` inside the zip. | Icons CC BY 4.0 |
| `carbon` | All IBM Carbon icons, from the SVGs of the npm package `@carbon/icons`, repacked into a zip by a small update script | Apache 2.0 |
| `40c3` | Deco icons, citizens and logos from the 40c3 style guide zip | CC0 |
| `attraktor` | Attraktor logo, colour and mono | Attraktor e.V. |

## Colouring

With `recolour = true`, every shape of the icon gets the design's icon colour
and other fill and stroke settings are removed. With `recolour = false`, the
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
- Web: file upload in the form. The file goes through the same normalising,
  with a size limit (default 256 KiB) and a limit on elements.
- Uploaded icons are not stored on the server. A link to a rendered image
  cannot carry an uploaded icon; the web page renders it from the form data.

## Search

The CLI and the web app can search icons by name, and for sources with
metadata (Font Awesome) by label and search terms: `wyltkm icons search cat`.
