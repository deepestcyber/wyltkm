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
| 3 | Font resolver | open |
| 4 | Bundled free fonts | open |
| 5 | `wyltkm config` and `wyltkm fonts` | open |

## 1. Config file and `Config`

Status: open

- Search order and format as in [configuration.md](../configuration.md);
  strict validation.
- `Library.from_config()` used by CLI and web.

## 2. Data directories

Status: open

- Search order from config, `WYLTKM_DATA_DIRS`, XDG, package data.
- Designs and icon sources from data directories, with override logging.

## 3. Font resolver

Status: open

- By file name in design dir, data dirs, system font dirs (recursively).
  No lookup by family name.
- `system_fonts = false` switches system lookup off.
- Fallback to ziafont's default font, with a warning.
- Cache resolved fonts per process.

## 4. Bundled free fonts

Status: open

- Pilowlava, Space Grotesk, Hack, Jersey 10 with licence files and licence
  records in `core/data/fonts/`. Hack and Jersey 10 come from the 40c3 style guide zip;
  Pilowlava and Space Grotesk from their upstream releases.
- `static/Pilowlava-Atome.otf` of the web app stays where the web needs it.

## 5. `wyltkm config` and `wyltkm fonts`

Status: open

- Print config file, data directories, and for each design the fonts it wants
  and where they resolve. The list of fonts users can pick follows in 0005.
