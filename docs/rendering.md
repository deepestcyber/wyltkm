# Rendering

How `wyltkm.core` turns a request into an image.

## Layout

The main column, from top to bottom, all parts as wide as the QR code:

1. Optional border (quiet zone) of 4 modules.
2. Top text (only if the request has one; may have several lines), scaled to
   the QR width, followed by the design's gap (default 2 modules).
3. QR code, with the icon centred in it (optional).
4. Bottom part, after the design's gap (default 2 modules): the request's
   own bottom text if it has one (in the design's bottom font, justified),
   nothing if the request switches it off, otherwise the design's (unless
   `type = "none"`): a text block (usually "WOULD YOU LIKE / TO KNOW MORE?", justified
   to full width) or an SVG graphic, scaled to the QR width. Text blocks are
   described in [designs.md](designs.md).
5. Optional border of 4 modules.

Gaps exist only next to a part that is there.

Optionally, a readable side text to the right of the main column (see below),
separated by the design's side gap (default 2 modules), inside the border.

The requested `width` is in px, default 250. The core accepts 50 to 10000;
the web app may set a lower maximum (`[web] max_width` in the config file,
default 4000).

The layout is computed in module units: every part's size follows from the
number of modules (text blocks are as wide as the QR code, so their height is
too). The finished layout is then scaled so the whole image is the requested
`width`, side text included. The height follows from the content.

### Readable side text

For people without a QR scanner, the image can show the content of the QR
code as readable text along its right side. It is opt-in per image
(`--side-text`, web checkbox); the design gives its default font and colour,
and the user may pick another font.

- The text is rotated by 90° and runs along the full height of the main
  column (top text to bottom line). It reads bottom to top by default, like a
  book spine; a design can set top to bottom.
- The font size is chosen so the text fills that height in one line, but
  capital letters are at most `max_size` modules high (default 3); shorter
  text then ends early.
- If one line would make the text smaller than the design's minimum size
  (`min_size`, in modules of cap height), the text wraps into several
  columns: as few as keep it at least that size. The breaks are then chosen
  so the columns are about equally long, which makes the text as large as
  possible. Breaks go after `/`, `?`, `&`, `=`, `.`, `-`, `_`, `#` or
  spaces, and at line breaks of the content; only when a piece is still too
  long, it breaks anywhere. Columns are left-aligned (seen in reading
  direction), with a gap of 1 module between columns.
- At most `max_columns` columns (design, default 4). Beyond that, the text
  gets smaller than `min_size` and the result carries a warning.
- The content is shown exactly as in the QR code, nothing shortened or
  prettified (no removed `https://`), so it can be typed in as it is.

Without a border the image has no quiet zone. That works when the image is
placed on a large enough plain area, which is how it is mostly used; the
design's background colour helps.

## QR code

- The module matrix comes from `qrcode` (no image factory, only the matrix).
- Error correction is always level H (about 30 % of the code can be lost),
  so the centre can be left empty for the icon. It is not configurable.
- The three finder patterns are drawn separately as an outer ring and an
  inner square, each with its own colour and shape from the design.
- Data modules are drawn in the design's module shape.
- With an icon, a centred square of modules is left out. Its side is
  `floor(0.3 × sqrt(n² − 128))` modules for a code of `n × n` modules (the
  128 are the finder patterns), made odd by subtracting 1 if needed so it
  is centred. This is the formula of 0.2.2, which assumes level H.
- The icon is fitted into that square less half a module on each side, by
  the extent of what it draws, not only by its declared viewBox
  ([icons.md](icons.md), "Normalising").

### Shapes

The design chooses shapes; all are built as path data:

| Element | Shapes |
| --- | --- |
| Data modules | `square`, `rounded` (corner radius as fraction of a module), `dot` |
| Finder ring | `square`, `rounded`, `circle` |
| Finder centre | `square`, `rounded`, `circle` |

A ring is one path with two subpaths and `fill-rule="evenodd"`, not a stroke.
Rounded corners and circles use arc or cubic Bézier commands.

Modules of one colour are merged into one `path` element with many subpaths,
which keeps files small and loads fast in laser cutter software.

## Paths only

Everything inside the QR code, and the text, is emitted as `path` elements
with fills:

- QR modules and finder patterns: generated as paths (above).
- Text: glyph outlines from ziafont as plain paths. No `<use>`, `<symbol>` or
  `<text>`.
- Icons: parsed, sanitised, and normalised: `rect`, `circle`, `ellipse`,
  `line`, `polyline` and `polygon` become paths; transforms stay on groups.
  Strokes, clip paths and gradients in icons are a known limit (see
  [icons.md](icons.md)).
- Bottom SVG graphics (if a design uses one): normalised in the same way.

The output has no external references, no scripts, no CSS classes; colours
are `fill` attributes. Strokes, clip paths and gradients from icons are kept
so the image looks right, and reported as a warning
([icons.md](icons.md)). Unless the request opts out, the file carries
licence info (SVG `<metadata>`, PNG `tEXt`; see [licences.md](licences.md)).

## Output formats

| Format | How |
| --- | --- |
| `svg` | The assembled SVG, size in px (`width`, `height`, `viewBox`) |
| `png` | The same SVG rasterised with cairosvg at the requested width |

The background is a filled path covering the whole image, like everything
else. A transparent background leaves it out (SVG) or makes the PNG
background transparent.

## Determinism

The same request with the same library gives byte-identical SVG output: fixed
number formatting, stable element order, no random ids. This allows
golden-file tests and caching in the web app.
