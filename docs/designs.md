# Designs

A design sets colours, fonts, QR shapes, the bottom part and defaults. Designs
are data, not code: one directory per design with a `design.toml` and its
assets. No design is special to the program; the built-in ones are designs
like any other.

## Where designs come from

Searched in this order, the first match by name wins:

1. `designs/` in each data directory ([configuration.md](configuration.md)),
   in configured order.
2. The built-in designs in the package (`wyltkm/core/data/designs/`).

An install can add designs or override a built-in one with the same name.
Overriding is logged.

The default design is set by `default_design` in the config file. Out of the
box it is `attraktor`, the design the project started with; any other design
can take its place.

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
module_radius = 0.3
finder_ring_shape = "rounded" # square | rounded | circle
finder_ring_radius = 1.0
finder_centre_shape = "rounded"
finder_centre_radius = 1.0

[top]                         # text block; the text comes from the request
fonts = ["AgencyFB-Bold.ttf"]
align = "center"
line_spacing = 1.05

[bottom]                      # text block with fixed text from the design
type = "text"
fonts = ["AgencyFB-Bold.ttf"]
lines = ["WOULD YOU LIKE", "TO KNOW [MORE]?"]
align = "justify"
line_spacing = 1.05

[side]                        # readable side text, when the user switches it on
fonts = ["Hack-Regular.ttf"]
direction = "up"
min_size = 1.5
max_columns = 4

[defaults]
icon = "attraktor:logo"
border = false
background = true

[licence]                     # for the design itself, see licences.md
name = "unclear"
holder = "Attraktor e.V."
```

### Keys

Lengths are in modules (the size of one QR module) unless stated otherwise.

| Key | Required | Default | Meaning |
| --- | --- | --- | --- |
| `name` | yes | | Must match the directory name; `a-z`, `0-9`, `-` |
| `title` | yes | | Shown in CLI and web |
| `description` | no | `""` | |
| `extends` | no | none | Design to inherit from |
| `default_scheme` | with schemes | | See "Colour schemes" |
| `colours.background` | yes | | |
| `colours.modules` | yes | | Data modules |
| `colours.finder_ring` | no | `modules` | |
| `colours.finder_centre` | no | `finder_ring` | |
| `colours.icon` | no | `modules` | Used when an icon is recoloured |
| `colours.top` | no | `modules` | Top text |
| `colours.bottom` | no | `top` | Bottom text, or a recoloured bottom SVG |
| `colours.highlight` | no | `bottom` | `[...]` in bottom text |
| `colours.side` | no | `top` | Readable side text |
| `qr.module_shape` | no | `square` | `square`, `rounded`, `dot` |
| `qr.module_radius` | no | `0.3` | Corner radius for `rounded` |
| `qr.finder_ring_shape` | no | `square` | `square`, `rounded`, `circle` |
| `qr.finder_ring_radius` | no | `1.0` | Outer corner radius for `rounded`; the inner edge's radius is one module less |
| `qr.finder_centre_shape` | no | `square` | `square`, `rounded`, `circle` |
| `qr.finder_centre_radius` | no | `1.0` | Corner radius for `rounded` |
| `top.fonts` | no | `[]` | Font file names, first one found is used; empty: ziafont's built-in font |
| `top.align` | no | `center` | `center`, `justify` |
| `top.line_spacing` | no | `1.05` | Line distance in font sizes |
| `bottom.type` | no | `none` | `text`, `svg`, `none` |
| `bottom.lines` | for `text` | | Lines of text, with `[...]` highlight markers |
| `bottom.fonts`, `.align`, `.line_spacing` | no | `[]`, `justify`, `1.05` | As for `top` |
| `bottom.svg` | for `svg` | | File relative to the design directory |
| `bottom.recolour` | no | `false` | For `svg`: fill all shapes with `colours.bottom` |
| `side.fonts` | no | `["Hack-Regular.ttf"]` | Default font for the side text |
| `side.direction` | no | `up` | `up`: reads bottom to top; `down`: top to bottom |
| `side.min_size` | no | `1.5` | Minimum cap height before wrapping into columns |
| `side.max_columns` | no | `4` | |
| `defaults.icon` | no | `none` | Icon when the request names none; `none` for no icon |
| `defaults.border` | no | `false` | |
| `defaults.background` | no | `true` | `false`: transparent |
| `licence` | no | none | Licence record ([licences.md](licences.md)); without it, "licence unknown" |

Colours are `#rrggbb`. A colour that is not set falls back as listed, so
colours added in later versions do not break existing designs.

### Text blocks

`[top]` and `[bottom]` (with `type = "text"`) are text blocks, rendered from
the font as glyph outlines:

- Every line gets the same font size. It is chosen so that the widest line,
  at the font's normal spacing, fills the QR width exactly.
- `align = "justify"`: shorter lines are stretched to the full width by
  spreading the extra space evenly over all gaps between glyphs (letters and
  words alike). This is how the "WOULD YOU LIKE / TO KNOW MORE?" line looks
  in the built-in designs.
- `align = "center"`: shorter lines keep normal spacing and are centred.
- `[...]` in `lines` marks text drawn in `colours.highlight`; the brackets
  are not drawn. `[[` and `]]` give a literal bracket. Text from the request
  (top text) is never parsed for markers.
- Kerning from the font is applied where ziafont provides it.

The readable side text is not a text block: it is sized along the image
height and wraps into columns, see [rendering.md](rendering.md). A monospace
font is a good default for it, since it keeps `l`, `1`, `I`, `0` and `O`
apart; the built-in designs use Hack.

Static graphics are possible with `type = "svg"`, for designs whose bottom is
a logo rather than text.

### Colour schemes

A design may offer several colour schemes. Then every scheme has a name,
including the main one, and `default_scheme` says which one is used when the
request names none. `[colours]` holds the values all schemes share; each
`[schemes.<name>]` sets a `title` and overrides colours:

```toml
default_scheme = "green"

[colours]                     # shared by all schemes
background = "#031202"
modules = "#75B54B"
# ...

[schemes.green]               # the main version
title = "Green"

[schemes.pink]
title = "Pink"
modules = "#EB5D9D"
finder_ring = "#EB6F83"

[schemes.light]
title = "Light"
background = "#DFEED5"
modules = "#3B5831"
```

- A design without schemes has only `[colours]`; a request naming a scheme
  for it is an error.
- The request names a scheme (`--scheme`, `scheme=`); without one,
  `default_scheme` is used. An unknown scheme is an error.
- The web app shows a second selection with the schemes when the chosen
  design has any; the default scheme is preselected.
- Text blocks follow the scheme's colours. A bottom SVG follows them only
  with `recolour = true`.

### Inheritance

- With `extends`, the parent design is loaded first and the child overrides
  it table by table, key by key. Chains are allowed; cycles are an error.
- Colours of a scheme are merged in this order, later wins: parent
  `[colours]`, child `[colours]`, parent `[schemes.<name>]`, child
  `[schemes.<name>]`. Fallbacks between colours (table above) apply after
  merging.
- The child inherits the parent's schemes and `default_scheme`, and may add
  schemes, override them, or set another `default_scheme`.
- Assets and fonts are looked up in the child's directory first, then in the
  parent's, up the chain.

### Rules

- Unknown keys are an error, so typos do not pass silently.
- Fonts are resolved as described in [configuration.md](configuration.md).
  When none of the listed fonts is found, ziafont's built-in font is used and
  a warning is reported to the caller (CLI: stderr, web: a note next to the
  preview).

## Built-in designs

| Name | Based on | Notes |
| --- | --- | --- |
| `attraktor` | | Default design out of the box. Attraktor blue and greys, Agency FB (not bundled, install it). Licence of the design unclear, marked as such. |
| `attraktor-bw` | `attraktor` | Black on white |
| `38c3` | | 38c3 style guide (CC0), Pilowlava |
| `38c3-light` | `38c3` | Space Grotesk on top |
| `38c3-lighter` | `38c3-light` | Space Grotesk on top and bottom |
| `40c3` | | 40c3 main version plus further colour schemes; worked out in [0003](development/0003-designs-planned.md) |

The 40c3 style guide (`40c3-styleguide-full-latest.zip`,
[source](https://events.ccc.de/congress/2026/infos/styleguide/)) gives a
palette of 14 colours, the fonts Hack and Jersey 10, and logos, deco icons,
citizens and patterns. Design and assets are CC0; the fonts have their own
licences. The style guide allows a lot of variation: the main version is the
design's default scheme, the other combinations are further schemes.

## Adding a design

1. Create `designs/<name>/design.toml` in a data directory (or in the package
   for a built-in one).
2. Put assets and fonts it needs next to it, or in `fonts/` of a data
   directory.
3. Check it with `wyltkm designs show <name>` and render a sample with
   `wyltkm render`.
