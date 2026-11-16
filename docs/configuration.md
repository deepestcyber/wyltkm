# Configuration

CLI and web read the same configuration. It is optional: without any config
file, the built-in designs, icons and bundled fonts work, and system fonts are
used.

## Config file

Searched in this order, the first one found is used:

1. The path in `WYLTKM_CONFIG`.
2. `$XDG_CONFIG_HOME/wyltkm/config.toml` (usually
   `~/.config/wyltkm/config.toml`).
3. `/etc/wyltkm/config.toml`.

```toml
default_design = "attraktor"
data_dirs = ["/srv/wyltkm"]   # searched before the default data dirs
system_fonts = true           # search the system's fonts too

[web]
max_width = 4000              # px; the core allows up to 10000
max_upload_bytes = 262144     # uploaded icons
max_upload_elements = 5000
max_upload_depth = 20
```

Unknown keys are an error.

## Data directories

A data directory may contain any of:

```
designs/<name>/design.toml   extra or overriding designs
icons/<source>.toml          extra icon sources (+ their zip or directory)
fonts/                       font files (.ttf, .otf)
```

Searched in this order:

1. `data_dirs` from the config file.
2. Directories in `WYLTKM_DATA_DIRS` (colon separated).
3. `$XDG_DATA_HOME/wyltkm` (usually `~/.local/share/wyltkm`).
4. `wyltkm` below each entry of `$XDG_DATA_DIRS` (default
   `/usr/local/share/wyltkm`, `/usr/share/wyltkm`).
5. The package's own data (built-in designs, icons, bundled fonts).

Directories that do not exist are skipped. `wyltkm config` prints the config
file and the data directories in use.

## Fonts

Designs list fonts by file name (`AgencyFB-Bold.ttf`). The list is tried in
order; for each name, the places below are searched in order, and the first
file found is used. Only when a name is found nowhere, the next name in the
list is tried. The places are:

1. The design's own directory, then those of its parents (`extends`).
2. `fonts/` of each data directory, in order (this includes the bundled
   fonts of the package as the last data directory).
3. System fonts, if `system_fonts` is true: by file name in the usual font
   directories and their subdirectories (`~/.local/share/fonts`, `~/.fonts`,
   `/usr/local/share/fonts`, `/usr/share/fonts`).

Only file names are matched, not font family names: a design must name the
file as it is usually distributed. Lookup by family name would need
fontconfig or reading the name tables of all font files, and is left out
until we need it.

When nothing matches, ziafont's built-in font is used and a warning is
returned with the image.

### Fonts users can pick

For the readable side text, users may pick a font other than the design's.
They can choose from all fonts found in `fonts/` of the data directories
(including the bundled ones), from system fonts if `system_fonts` is true,
and the side text default font of every design (wherever it was found).
The request names the font by file name; any other name is rejected. On a
hosted web app, `system_fonts = false` keeps this list to the fonts the
operator put in place.

### Bundled fonts

Fonts with a free licence that allows redistribution ship in the package,
each with its licence file and a licence record ([licences.md](licences.md)):
Pilowlava, Space Grotesk, Hack, Jersey 10. The exact files and their origin
are listed in [0001](development/0001-core-split-active.md), part 4.

Agency FB, the font of the Attraktor design, is not free. Install it in a
font directory (for a server: `fonts/` of a data directory; for local work:
the user's font directory works through system fonts).

### Server installs

For a hosted web app, set `system_fonts = false` and put all needed fonts in
`fonts/` of a data directory, so the output does not depend on what the host
happens to have installed.
