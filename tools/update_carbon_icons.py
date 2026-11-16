#!/usr/bin/env python3
"""Build the Carbon icon zip from the npm package ``@carbon/icons``.

Downloads the pinned version of the package tarball from the npm registry and
writes ``carbon-icons-<version>.zip`` with the 32 px SVGs (``svg/32/``), the
licence and a slim ``metadata.json`` (name, label, aliases, file of each
icon). Then adjust ``carbon.toml`` (path, prefix, title) if the version
changed and remove the old zip.

Usage: python tools/update_carbon_icons.py [VERSION] [OUTPUT_DIR]
"""

from __future__ import annotations

import io
import json
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

VERSION = "11.92.0"
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "src" / "wyltkm" / "core" / "data" / "icons"
URL = "https://registry.npmjs.org/@carbon/icons/-/icons-{version}.tgz"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)  # reproducible zip


def main() -> int:
    version = sys.argv[1] if len(sys.argv) > 1 else VERSION
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    with urllib.request.urlopen(URL.format(version=version)) as response:
        data = response.read()
    tar = tarfile.open(fileobj=io.BytesIO(data), mode="r:gz")
    files: dict[str, bytes] = {}
    for member in tar.getmembers():
        name = member.name
        if not member.isfile():
            continue
        if name.startswith("package/svg/32/") and name.endswith(".svg"):
            files["svg/32/" + name[len("package/svg/32/"):]] = tar.extractfile(member).read()
        elif name in ("package/LICENSE", "package/metadata.json"):
            files[name[len("package/"):]] = tar.extractfile(member).read()
    meta = json.loads(files.pop("metadata.json"))
    slim = []
    for icon in meta["icons"]:
        for asset in icon.get("assets", []):
            if asset.get("size") == 32 and f"svg/{asset['filepath']}" in files:
                slim.append({"file": asset["filepath"], "label": icon.get("friendlyName", ""),
                             "terms": icon.get("aliases", [])})
    files["metadata.json"] = json.dumps({"version": version, "icons": slim}, indent=0,
                                        sort_keys=True).encode()
    out = out_dir / f"carbon-icons-{version}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, files[name])
    print(f"{out}: {sum(1 for n in files if n.endswith('.svg'))} icons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
