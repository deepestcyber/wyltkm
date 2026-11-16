# Configuration and fonts

Status: completed (2026-11-16)

Config file, data directories and font lookup, so installs have a defined
place for fonts, designs and icon sources, and the CLI uses system fonts.

Background: [configuration.md](../configuration.md).

Status values: `open`, `in progress`, `done`.

| # | Part | Status |
| --- | --- | --- |
| 1 | Config file and `Config` | done |
| 2 | Data directories | done |
| 3 | Font resolver: data directories and switch | done |
| 4 | `wyltkm config` and `wyltkm fonts` | done |

## 1. Config file and `Config`

Status: done (2026-11-16)

- Search order and format as in [configuration.md](../configuration.md);
  strict validation. `default_design` (default `attraktor`), `system_fonts`,
  `data_dirs`, `[web]` limits.
- `Library.from_config()` used by CLI and web.

Done:

- `wyltkm.core.config`: `load()` returns a `Config` (`path`, `default_design`,
  `system_fonts`, `candidates` with origin of each data directory,
  `data_dirs`, `web`). `WYLTKM_CONFIG` naming a missing file is an error.
  Relative `data_dirs` are relative to the config file.
- `Library.from_config()`; CLI and web use it. Errors in the config file give
  CLI exit code 4.

## 2. Data directories

Status: done (2026-11-16)

- Search order from config, `WYLTKM_DATA_DIRS`, XDG, package data.
- Designs and icon sources from data directories, with override logging.

Done:

- Existing directories only, without duplicates. Designs, icon sources and
  fonts of data directories come before the package's own.

## 3. Font resolver: data directories and switch

Status: done (2026-11-16)

- Extends the basic lookup of 0001 (part 4) to the full order in
  [configuration.md](../configuration.md): design directories, `fonts/` of
  the data directories, system font directories (recursively). File names
  only, no family names.
- `system_fonts = false` switches system lookup off.
- `<fontfile>.licence.toml` read for fonts in data directories.
- Cache resolved fonts per process.

Done:

- The resolver of 0001 already took the font directories and the switch;
  `available()` lists fonts of the font directories. Licence records next to
  font files are read wherever the font is.
- Upload limits from `[web]` go to the library (`upload_max_elements`,
  `upload_max_depth`) and the web app (`max_width`, `max_upload_bytes`).

## 4. `wyltkm config` and `wyltkm fonts`

Status: done (2026-11-16)

- Print config file, data directories, and for each design the fonts it wants
  and where they resolve. The list of fonts users can pick follows in 0005.

Done:

- `wyltkm config` shows every candidate data directory as used, missing or
  duplicate. `wyltkm fonts` lists the fonts of the font directories with
  their licence, and per design where each font is found.
- Tests isolate the environment (`tests/conftest.py`), so no config, data
  directory or system font of the machine leaks in.

