# Icon sources

Status: completed (2026-11-16)

All free Font Awesome icons from the release zip, the full Carbon set, the 40c3
assets, install-defined sources, uploads and search, in CLI and web.

Background: [icons.md](../icons.md).

Status values: `open`, `in progress`, `done`.

| # | Part | Status |
| --- | --- | --- |
| 1 | `zip` source type and source TOML files | done |
| 2 | Font Awesome from the release zip, with metadata | done |
| 3 | Carbon | done |
| 4 | 40c3 assets | done |
| 5 | Sources from data directories | done |
| 6 | Search | done |
| 7 | Uploaded icons | done |
| 8 | CLI commands and licences | done |

## 1. `zip` source type and source TOML files

Status: done (2026-11-16)

- Index of the zip's members below `prefix` at startup; members read on
  demand, small LRU cache of normalised icons.
- Source TOML format as in [icons.md](../icons.md).

Done:

- `zip` sources read their member list at startup and members on demand.
  New key `include` (folders below `prefix`). Normalised icons are cached in
  the library (LRU, 256 icon and colour pairs; callers get copies).

## 2. Font Awesome from the release zip

Status: done (2026-11-16)

- `fontawesome-free-7.3.1-web.zip`, styles `solid`, `regular`, `brands`.
- Labels and search terms from `metadata/icons.json`.
- Remove `res/awesome`. Clean break: Font Awesome 7 names are used as they
  are, no mapping from old names.
- Update procedure documented: replace the zip, adjust `fa.toml`.

Done:

- 2883 icons (the zip also has alias files of older names, e.g.
  `arrow-alt-circle-up`; they are icons like the others). Metadata is read
  lazily on the first search.

## 3. Carbon

Status: done (2026-11-16)

- Carbon is Apache 2.0. The npm package `@carbon/icons` contains all icons
  as SVG files (`svg/32/`). A small update script downloads a pinned version
  of the package tarball and repacks the SVGs, the licence and the metadata
  into a zip, which is committed like the Font Awesome zip. Remove the
  current subset.
- Carbon SVGs use `<style>` and primitives; check normalising handles them.

Done:

- `tools/update_carbon_icons.py`, pinned to 11.92.0: `carbon-icons-11.92.0.zip`
  (1.2 MB, 2779 icons, `LICENSE`, slim `metadata.json` with labels and
  aliases), written reproducibly. Names are lower-cased; of `3D-Cursor` and
  `3D-cursor`-like pairs the first one wins.

## 4. 40c3 assets

Status: done (2026-11-16)

- Source `40c3` on the style guide zip: `Assets/Icons_Deco`, `Assets/Citizens`,
  `Assets/Logos`. Names from the file-name rule ([icons.md](../icons.md)),
  e.g. `icons-deco/icon-cat`, `citizens/blahaj`, `logos/40c3-logo-a`; a
  `rename` table only where that is unreadable.
- These are multi-coloured: `recolour = false`, with `recolour_except` for
  folders that should take the design colour, if any.
- Licence CC0, from the style guide page; two assets use a clip path and
  get the "not laser-friendly" warning.

Done:

- `include = ["Icons_Deco/", "Citizens/", "Logos/"]`; names like
  `icons-deco/icon-cat`, `citizens/blahaj`, `logos/40c3-logo-a`, no `rename`
  needed. The logos are single-coloured and take the design's colour
  (`recolour_except = ["logos/"]`); deco icons and citizens mix colours and
  keep them.
- The `40c3` design now has `40c3:logos/40c3-logo-a` as default icon: pale on
  the dark schemes, dark on the light ones.

## 5. Sources from data directories

Status: done (2026-11-16)

- `icons/<source>.toml` in data directories, override of built-ins.

Done:

- Data directories came with 0002; zip sources work there the same way.

## 6. Search

Status: done (2026-11-16)

- Search by name and metadata across sources, ranked (exact name, name
  prefix, label, search term).
- Used by `wyltkm icons search`.
- `/api/icons` and `/icons/<source>/<name>.svg` built here
  ([web.md](../web.md)); the web picker using them is 0006.

Done:

- `IconRegistry.search()`; all words must match, ranked as in
  [icons.md](../icons.md). `/api/icons`, `/api/icon-sources` and
  `/icons/<source>/<name>.svg?colour=`. The web form got an icon name field
  and a server-side search with small previews instead of the drop-down,
  which would have had 5700 entries.

## 7. Uploaded icons

Status: done (2026-11-16)

- `Request` carries either an icon name or icon SVG bytes.
- CLI `--icon-file`; web upload (wired into the UI in 0006).
- Limits: size, number of elements, nesting depth.
- Tests with hostile SVGs (entities, external references, scripts, huge
  files).

Done:

- Mostly in 0001 already; here CLI `--icon-file`. Hostile SVG tests in
  `tests/test_svg.py`, CLI and web tests for uploads.

## 8. CLI commands and licences

Status: done (2026-11-16)

- `wyltkm icons`, `icons list`, `icons search`, `icons show`.
- Licence records per source, shown by `wyltkm licences` and the web
  licences page.

Done:

- `wyltkm icons list SOURCE [FOLDER]`, `icons search`, `icons show [-c
  COLOUR] [-o FILE]` (prints the licence to stderr); `render_icon()` in the
  core for CLI and web.
- The three zips (Font Awesome, Carbon, 40c3) are committed with this unit.

## Open questions

- None at the moment. (Per-icon or per-folder recolouring is answered by
  `recolour_except` in the source file, added in 0001 for the Attraktor
  logos.)
