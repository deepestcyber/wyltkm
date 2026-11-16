# Icon sources

Status: planned

All free Font Awesome icons from the release zip, the full Carbon set, the 40c3
assets, install-defined sources, uploads and search, in CLI and web.

Background: [icons.md](../icons.md).

Status values: `open`, `in progress`, `done`.

| # | Part | Status |
| --- | --- | --- |
| 1 | `zip` source type and source TOML files | open |
| 2 | Font Awesome from the release zip, with metadata | open |
| 3 | Carbon | open |
| 4 | 40c3 assets | open |
| 5 | Sources from data directories | open |
| 6 | Search | open |
| 7 | Uploaded icons | open |
| 8 | CLI commands and licences | open |

## 1. `zip` source type and source TOML files

Status: open

- Index of the zip's members below `prefix` at startup; members read on
  demand, small LRU cache of normalised icons.
- Source TOML format as in [icons.md](../icons.md).

## 2. Font Awesome from the release zip

Status: open

- `fontawesome-free-7.3.1-web.zip`, styles `solid`, `regular`, `brands`.
- Labels and search terms from `metadata/icons.json`.
- Remove `res/awesome`. Clean break: Font Awesome 7 names are used as they
  are, no mapping from old names.
- Update procedure documented: replace the zip, adjust `fa.toml`.

## 3. Carbon

Status: open

- Carbon is Apache 2.0. The npm package `@carbon/icons` contains all icons
  as SVG files (`svg/32/`). A small update script downloads a pinned version
  of the package tarball and repacks the SVGs, the licence and the metadata
  into a zip, which is committed like the Font Awesome zip. Remove the
  current subset.
- Carbon SVGs use `<style>` and primitives; check normalising handles them.

## 4. 40c3 assets

Status: open

- Source `40c3` on the style guide zip: `Assets/Icons_Deco`, `Assets/Citizens`,
  `Assets/Logos`, with readable names (`icon-cat`, `citizen-blahaj`,
  `logo-0`).
- These are multi-coloured: `recolour = false` by default, maybe a
  per-icon or per-folder override.
- Licence CC0, from the style guide page; two assets use a clip path and
  get the "not laser-friendly" warning.

## 5. Sources from data directories

Status: open

- `icons/<source>.toml` in data directories, override of built-ins.

## 6. Search

Status: open

- Search by name and metadata across sources, ranked (exact name, name
  prefix, label, search term).
- Used by `wyltkm icons search` and `/api/icons`.

## 7. Uploaded icons

Status: open

- `Request` carries either an icon name or icon SVG bytes.
- CLI `--icon-file`; web upload (wired into the UI in 0006).
- Limits: size, number of elements, nesting depth.
- Tests with hostile SVGs (entities, external references, scripts, huge
  files).

## 8. CLI commands and licences

Status: open

- `wyltkm icons`, `icons list`, `icons search`, `icons show`.
- Licence and attribution per source available to the web footer.
