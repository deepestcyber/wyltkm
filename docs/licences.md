# Licences

A generated image is made of parts with their own licences: the icon, assets
of the design (logos, graphics), and the font outlines of the text.
Whoever uses an image should know the conditions, e.g. that a Font Awesome
icon needs attribution (CC BY 4.0). WYLTKM therefore tracks licences per part
and reports them with every image.

## Licence records

Every icon source, design and bundled font has a licence record:

```toml
[licence]
name = "CC-BY-4.0"                     # SPDX id where one exists, else a short name
url = "https://fontawesome.com/license/free"
holder = "Fonticons, Inc."
attribution = "Icon from Font Awesome Free, https://fontawesome.com, CC BY 4.0"
requires_attribution = true            # default false
file = "LICENSE.txt"                   # optional: licence text next to the part
```

`requires_attribution` is set by whoever writes the record; for the known
licences below, the "Attribution" column says what we set.

- Icon sources have it in their source TOML ([icons.md](icons.md)).
- Designs have it in `design.toml`, for their own assets.
- Fonts: one `<fontfile>.licence.toml` next to each font file (e.g.
  `Hack-Regular.ttf.licence.toml`), for bundled fonts and fonts of the
  install alike. A font without a record (always the case for system fonts)
  is reported as "licence unknown".

## Per render

The render result lists the records of the parts actually used: the design
(always, since its look is used), the chosen icon's source, the fonts used for
text, including the side text font. Sorted, without duplicates.
- **In the image file** (on by default, opt-out):
  - SVG: the records go into a `<metadata>` element (plain text and RDF with
    the licence URLs). It does not affect drawing or laser cutting.
  - PNG: the attribution text goes into a `tEXt` chunk.

  The request field `licence_metadata` (default true) switches it off: CLI
  `--no-licence-metadata`, web checkbox and parameter `licence_metadata=0`.
  The licence report in CLI and web is shown either way.
- **CLI**: after rendering, a short summary goes to stderr when any part
  requires attribution or its licence is "unclear" or unknown; `--licences` always prints the full list.
  `wyltkm licences` lists the licences of all sources, designs and fonts.
- **Web**: a box under the preview shows the licences of the current image,
  with the attribution text ready to copy. A licences page lists all
  sources, designs and fonts.

## Known licences

| Part | Licence | Attribution |
| --- | --- | --- |
| Font Awesome Free icons | CC BY 4.0 | required |
| IBM Carbon icons | Apache 2.0 | not required for images; the licence text ships with the zip |
| 40c3 style guide assets | CC0 ([source](https://events.ccc.de/congress/2026/infos/styleguide/)) | not required |
| Hack (font) | MIT/Bitstream Vera licence, file in the style guide zip | — |
| Jersey 10 (font) | SIL OFL 1.1, file in the style guide zip | — |
| Pilowlava, Space Grotesk (fonts) | SIL OFL 1.1 | — |
| Attraktor design and logo | "unclear", holder Attraktor e.V.; shown as such until clarified | unclear |
| 38c3 style | CC0 | not required |
| Agency FB (font, not bundled) | commercial, install's own licence | — |
| DejaVu Sans (fallback font, from ziafont) | Bitstream Vera licence | — |

Font licences cover the use of the font; glyph outlines in a graphic are
normally allowed by them. They are listed so users can check.

The 40c3 zip itself carries only the font licences. The CC0 statement from
the style guide page is kept in a `LICENCE.md` next to the zip in the
repository.
