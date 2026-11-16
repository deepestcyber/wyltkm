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
align = "justify"
gap = 2                       # to the QR code, in modules
line_gap = 2                  # between lines; default: gap

[bottom]                      # text block with fixed text from the design
type = "text"
fonts = ["AgencyFB-Bold.ttf"]
lines = ["WOULD YOU LIKE", "TO KNOW [MORE]?"]
align = "justify"
gap = 2                       # to the QR code, in modules
line_gap = 2                  # between lines; default: gap

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
| `order` | no | `100` | Position in lists (CLI, web): lower first, then by name; the default design is always first |
| `extends` | no | none | Design to inherit from |
| `default_scheme` | with schemes | | See "Schemes" |
| `colours.background` | yes | | |
| `colours.modules` | yes | | Data modules |
| `colours.finder_ring` | no | `modules` | |
| `colours.finder_centre` | no | `finder_ring` | |
| `colours.icon` | no | `modules` | Used when an icon is recoloured |
| `colours.top` | no | `modules` | Top text |
| `colours.bottom` | no | `top` | Bottom text, or a recoloured bottom SVG |
| `colours.highlight` | no | `bottom` | `[...]` in top and bottom text |
| `colours.side` | no | `top` | Readable side text |
| `qr.module_shape` | no | `square` | `square`, `rounded`, `dot` |
| `qr.module_radius` | no | `0.3` | Corner radius for `rounded` |
| `qr.finder_ring_shape` | no | `square` | `square`, `rounded`, `circle` |
| `qr.finder_ring_radius` | no | `1.0` | Outer corner radius for `rounded`; the inner edge's radius is one module less |
| `qr.finder_centre_shape` | no | `square` | `square`, `rounded`, `circle` |
| `qr.finder_centre_radius` | no | `1.0` | Corner radius for `rounded` |
| `top.fonts` | no | `[]` | Font file names, first one found is used; empty: ziafont's built-in font |
| `top.align` | no | `justify` | `justify`, `center`; the request can switch it |
| `top.gap` | no | `2` | Space between top text and QR code |
| `top.line_gap` | no | `gap` | Space between lines, from the ink of one line to the ink of the next |
| `bottom.type` | no | `none` | `text`, `svg`, `none` |
| `bottom.lines` | for `text` | | Lines of text, with `[...]` highlight markers |
| `bottom.fonts`, `.align` | no | `[]`, `justify` | As for `top` |
| `bottom.gap`, `.line_gap` | no | `2`, `gap` | As for `top`; `gap` also applies to a bottom graphic |
| `bottom.svg` | for `svg` | | File relative to the design directory |
| `bottom.recolour` | no | `false` | For `svg`: fill all shapes with `colours.bottom` |
| `side.fonts` | no | `["Hack-Regular.ttf"]` | Default font for the side text |
| `side.direction` | no | `up` | `up`: reads bottom to top; `down`: top to bottom |
| `side.gap` | no | `2` | Space between the main column and the side text |
| `side.min_size` | no | `1.5` | Minimum cap height before wrapping into columns |
| `side.max_size` | no | `3` | Maximum cap height, so short content does not get huge letters |
| `side.max_columns` | no | `4` | |
| `defaults.icon` | no | `none` | Icon when the request names none; `none` for no icon |
| `schemes.<name>.title` | yes | | Name of the scheme in CLI and web |
| `schemes.<name>.default_icon` | no | `defaults.icon` | Default icon of this scheme, e.g. a mono logo for a black and white scheme |
| `schemes.<name>.fonts.top`, `.bottom`, `.side` | no | the design's | Fonts of this scheme, lists of file names |
| `schemes.<name>.<colour>` | no | from `[colours]` | Any colour key, as in `[colours]` |
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
- Both texts are justified by default. A request can switch each to centred
  or back (`top_justify`, `bottom_justify`); very short lines spread wide
  when justified, so centring suits them better.
- `[...]` marks text drawn in `colours.highlight`; the brackets are not
  drawn. `[[` and `]]` give a literal bracket. This works in the design's
  `lines`, in the top text of the request, and in an own bottom text of the
  request. Unbalanced brackets are an error.
- Lines are spaced by the ink: `line_gap` is the space from the lowest point
  of one line to the highest point of the next, the same way `gap` is
  measured to the QR code. With the default (`line_gap` = `gap`), the space
  between the lines equals the space to the code, whatever the font's own
  line height. An empty line between two lines takes the height of a capital
  letter plus one `line_gap`.
- Kerning from the font is applied where ziafont provides it.

The readable side text is not a text block: it is sized along the image
height and wraps into columns, see [rendering.md](rendering.md). A monospace
font is a good default for it, since it keeps `l`, `1`, `I`, `0` and `O`
apart; the built-in designs use Hack.

Static graphics are possible with `type = "svg"`, for designs whose bottom is
a logo rather than text.

### Schemes

A design may offer several schemes: variants that change its colours, its
fonts or its default icon, while the rest of the design stays. Then every
scheme has a name, including the main one, and `default_scheme` says which
one is used when the request names none. `[colours]` holds the values all
schemes share; each `[schemes.<name>]` sets a `title` and overrides colours:

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
- The web app shows the schemes of the chosen design as chips with a colour
  dot and the title; the default scheme is preselected.
- A scheme may set fonts in a `fonts` table, with `top`, `bottom` and
  `side` as lists of font file names, e.g.
  `fonts = { top = ["SpaceGrotesk-Regular.otf"] }`. Fonts it does not set
  are the design's. Alignment and gaps stay those of the design. (`top` and
  `bottom` directly in a scheme are colours, as in `[colours]`.)
- Text blocks follow the scheme's colours. A bottom SVG follows them only
  with `recolour = true`.
- Besides colours, a scheme may set `default_icon`, used when the request
  names no icon; `icon` in a scheme is the icon colour, like in `[colours]`.

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
| `attraktor` | | Default design out of the box. Agency FB (not bundled, install it). Schemes `colour` (default: Attraktor blue and greys, colour logo) and `bw` (black on white, mono logo). Licence of the design unclear, marked as such. |
| `38c3` | | 38c3 style guide (CC0). Schemes with the same colours and different fonts: `pilowlava` (default, Pilowlava everywhere), `light` (Space Grotesk on top), `lighter` (Space Grotesk on top and bottom) |
| `40c3` | | 40c3 "Model Citizens", Jersey 10, square modules, the 40c3 logo as icon. Thirteen schemes (including `bw` for engraving), default `green` |

The 40c3 style guide (`40c3-styleguide-full-latest.zip`,
[source](https://events.ccc.de/congress/2026/infos/styleguide/)) gives a
palette of 14 colours, the fonts Hack and Jersey 10, and logos, deco icons,
citizens and patterns. Design and assets are CC0; the fonts have their own
licences. The style guide allows a lot of variation: the main version is the
design's default scheme, the other combinations are further schemes.

The style guide's "Tricolore" is A (`#DFEED5`), B (`#031202`) and one colour
of your choice; its key colours are 0 (green), A and B. The `40c3` design
follows that:

- Dark schemes on B, one per palette colour that stands out on B: `green`
  (0, the main version), `teal` (1), `lavender` (2), `lilac` (3), `pink`
  (4), `rose` (5), `orange` (6), `yellow` (7), `sage` (8), `taupe` (10). The
  colour is used for modules, finder rings, top text and the highlighted
  "MORE"; A for finder centres, icon and the bottom line.
- Light schemes on A: `light` with dark green (9) and B, `light-brown` with
  brown (11) and B. Colours 9 and 11 are too dark for the dark schemes.
- `bw`: black on white, for engraving and plain print; the logo turns black
  too.
- Headings in the style guide are Jersey 10, so are top text and bottom
  line; square modules and finder patterns go with its pixel look.
- Every scheme keeps a contrast of at least 4.5 between code and background,
  and is tested to scan.

## Adding a design

1. Pick a data directory (see [configuration.md](configuration.md); for
   your own user `~/.local/share/wyltkm`) and create
   `designs/<name>/design.toml` in it. For a built-in design, use
   `src/wyltkm/core/data/designs/` instead. `<name>`: lower case letters,
   digits and `-`.
2. Write the file: at least `name`, `title`, `colours.background` and
   `colours.modules`; everything else has defaults (key table above). Start
   from a built-in design, or use `extends` to change only a few values of
   one.
3. Put fonts the design needs next to `design.toml` or into `fonts/` of the
   data directory, by file name, each with a `<fontfile>.licence.toml`
   ([licences.md](licences.md)). Add a `[licence]` table for the design.
4. Check it: `wyltkm designs show <name>` shows the resolved values, where
   each font is found, and the contrast of the code against the background
   (below 3 it is marked LOW). Mistakes in the file are reported with the
   file name.
5. Look at it: `wyltkm designs show <name> --preview -o preview.png` (add a
   scheme name after `--preview` for a scheme), or render a real code with
   `wyltkm render`. Scan it with a phone.
6. For a built-in design, add it to the tests: a golden-file case in
   `tests/test_render.py` and the decode test in `tests/test_qr.py`.
