# Configuration and fonts

Status: planned

Config file, data directories and font lookup, so installs have a defined
place for fonts, designs and icon sources, and the CLI uses system fonts.

Background: [configuration.md](../configuration.md).

Status values: `open`, `in progress`, `done`.

| # | Part | Status |
| --- | --- | --- |
| 1 | Config file and `Config` | open |
| 2 | Data directories | open |
| 3 | Font resolver: data directories and switch | open |
| 4 | `wyltkm config` and `wyltkm fonts` | open |

## 1. Config file and `Config`

Status: open

- Search order and format as in [configuration.md](../configuration.md);
  strict validation. `default_design` (default `attraktor`), `system_fonts`,
  `data_dirs`, `[web]` limits.
- `Library.from_config()` used by CLI and web.

## 2. Data directories

Status: open

- Search order from config, `WYLTKM_DATA_DIRS`, XDG, package data.
- Designs and icon sources from data directories, with override logging.

## 3. Font resolver: data directories and switch

Status: open

- Extends the basic lookup of 0001 (part 4) to the full order in
  [configuration.md](../configuration.md): design directories, `fonts/` of
  the data directories, system font directories (recursively). File names
  only, no family names.
- `system_fonts = false` switches system lookup off.
- `<fontfile>.licence.toml` read for fonts in data directories.
- Cache resolved fonts per process.

## 4. `wyltkm config` and `wyltkm fonts`

Status: open

- Print config file, data directories, and for each design the fonts it wants
  and where they resolve. The list of fonts users can pick follows in 0005.
