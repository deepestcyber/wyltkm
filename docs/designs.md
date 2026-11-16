# Designs

A design sets colours, fonts, QR shapes, the bottom part and defaults. Designs
are data, not code: one directory per design with a `design.toml` and its
assets.

## Where designs come from

Searched in this order, the first match by name wins:

1. `designs/` in each data directory ([configuration.md](configuration.md)),
   in configured order.
2. The built-in designs in the package (`wyltkm/core/data/designs/`).

An install can add designs or override a built-in one with the same name.
Overriding is logged.

The default design is `attraktor`, unless the config file sets
`default_design`.

## Format

```toml
# designs/attraktor/design.toml
name = "attraktor"            # must match the directory name
title = "Attraktor"
description = "Attraktor e.V. blue and grey"
extends = ""                  # optional: name of a design to inherit from

[colours]
background = "#ffffff"
modules = "#9b9c9e"
finder_ring = "#67b8dc"
finder_centre = "#4b4b4d"
icon = "#4b4b4d"
top = "#4b4b4d"
bottom = "#4b4b4d"
highlight = "#67b8dc"         # marked words in text blocks, e.g. "MORE"
side = "#4b4b4d"              # readable side text

[qr]
module_shape = "rounded"      # square | rounded | dot
module_radius = 0.3           # fraction of a module, for rounded
finder_ring_shape = "rounded" # square | rounded | circle
finder_centre_shape = "rounded"
finder_radius = 1.0           # in modules, for rounded

[top]                         # text block; the text comes from the request
fonts = ["AgencyFB-Bold.ttf"] # font file names; first one found is used
align = "center"              # center | justify
line_spacing = 1.05           # in font size

[bottom]                      # text block with fixed text from the design
type = "text"                 # text | svg | none
fonts = ["AgencyFB-Bold.ttf"]
lines = ["WOULD YOU LIKE", "TO KNOW [MORE]?"]   # [..] uses colours.highlight
align = "justify"
line_spacing = 1.05
# for type = "svg" (a graphic instead of text):
# svg = "bottom.svg"          # relative to the design directory
# recolour = false            # true: fill all shapes with colours.bottom

[side]                        # readable side text, when the user switches it on
fonts = ["Hack-Regular.ttf"]  # default font; the user may pick another one
direction = "up"              # up: reads bottom to top | down: top to bottom
min_size = 1.5                # minimum cap height in modules before wrapping
max_columns = 4

[defaults]
icon = "attraktor:logo"       # icon when the request names none; "" for none
border = false
background = true

[licence]                     # for the design itself, see licences.md
name = "unclear"
holder = "Attraktor e.V."
```

### Text blocks

`[top]` and `[bottom]` (with `type = "text"`) are text blocks, rendered from
the font as glyph outlines:

- Every line gets the same font size. It is chosen so that the widest line,
  at the font's normal spacing, fills the QR width exactly.
- `align = "justify"`: shorter lines are stretched to the full width by
  spreading the extra space evenly over all gaps between glyphs (letters and
  words alike). This is how the "WOULD YOU LIKE / TO KNOW MORE?" line looks
  in all built-in designs.
- `align = "center"`: shorter lines keep normal spacing and are centred.
- `[...]` in `lines` marks text drawn in `colours.highlight`; the brackets
  are not drawn. Text from the request (top text) is never parsed for
  markers.
- Kerning from the font is applied where ziafont provides it.

The readable side text is not a text block: it is sized along the image
height and wraps into columns, see [rendering.md](rendering.md). A monospace
font is a good default for it, since it keeps `l`, `1`, `I`, `0` and `O`
apart; the built-in designs use Hack.

Static graphics are still possible with `type = "svg"`, for designs whose
bottom is a logo rather than text.

### Colour schemes

A design may offer several colour schemes. The `[colours]` table is the main
scheme; each `[schemes.<name>]` table overrides some or all colours:

```toml
[colours]                     # main scheme, used when none is chosen
background = "#031202"
modules = "#75B54B"
# ...

[schemes.pink]
title = "Pink"
modules = "#EB5D9D"
finder_ring = "#EB6F83"

[schemes.light]
title = "Light"
background = "#DFEED5"
modules = "#3B5831"
# ...
```

- The request names a scheme (`--scheme`, `scheme=`); without one, the main
  colours are used.
- The web app shows a second selection with the schemes when the chosen
  design has any; the main scheme is preselected.
- A child design inherits its parent's schemes and may add or override
  schemes.
- Text blocks follow the scheme's colours. A bottom SVG follows them only
  with `recolour = true`.

Rules:

- With `extends`, the parent design is loaded first and its values are
  overridden table by table, key by key. Assets are looked up in the child's
  directory first, then in the parent's. Chains are allowed; cycles are an
  error.
- Unknown keys are an error, so typos do not pass silently.
- Colours are `#rrggbb`. Every colour must be set (directly or inherited).
- Fonts are resolved as described in [configuration.md](configuration.md).
  When none of the listed fonts is found, a fallback font is used and a
  warning is reported to the caller (CLI: stderr, web: a note next to the
  preview).

## Built-in designs

| Name | Based on | Notes |
| --- | --- | --- |
| `attraktor` | | Default. Attraktor blue and greys, Agency FB (not bundled). Licence of the design unclear, marked as such. |
| `attraktor-bw` | `attraktor` | Black on white |
| `38c3` | | 38c3 style guide (CC0), Pilowlava |
| `38c3-light` | `38c3` | Space Grotesk on top |
| `38c3-lighter` | `38c3-light` | Space Grotesk on top and bottom |
| `40c3` | | Main 40c3 version, plus colour schemes from the 40c3 palette; details in the designs plan |

The 40c3 style guide (`40c3-styleguide-full-latest.zip`,
[source](https://events.ccc.de/congress/2026/infos/styleguide/)) gives a
palette of 14 colours, the fonts Hack and Jersey 10, and logos, deco icons,
citizens and patterns. Design and assets are CC0; the fonts have their own
licences. The style guide allows a lot of variation: the main version is the
design's `[colours]`, and the other combinations are its colour schemes.

## Adding a design

1. Create `designs/<name>/design.toml` in a data directory (or in the package
   for a built-in one).
2. Put assets next to it.
3. Check it with `wyltkm designs show <name>` and render a sample with
   `wyltkm render`.
