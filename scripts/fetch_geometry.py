"""Fetch and pin Natural Earth country geometry for the local data build.

Run this only when intentionally refreshing the source. The website serves a
small, committed derivative and never calls GitHub at runtime.
"""

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research" / "validation-data"
REPOSITORY = "https://api.github.com/repos/nvkelso/natural-earth-vector"
SOURCE_PATH = "geojson/ne_110m_admin_0_countries.geojson"
RELEASE = "v5.1.1"


def read_url(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "FIT3179-board-games-prototype"})
    with urlopen(request, timeout=45) as response:
        return response.read()


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    commit = json.loads(read_url(f"{REPOSITORY}/commits/{RELEASE}"))
    sha = commit["sha"]
    base = f"https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{sha}"
    payload = read_url(f"{base}/{SOURCE_PATH}")
    geometry = json.loads(payload)
    assert geometry["type"] == "FeatureCollection" and len(geometry["features"]) > 150
    version = read_url(f"{base}/VERSION").decode("utf-8").strip()
    source = RAW / "natural-earth-countries.geojson"
    source.write_bytes(payload)
    manifest = {
        "organisation": "Natural Earth",
        "repository": "https://github.com/nvkelso/natural-earth-vector",
        "source_url": f"{base}/{SOURCE_PATH}",
        "source_path": SOURCE_PATH,
        "commit": sha,
        "version": version,
        "release": RELEASE,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "feature_count": len(geometry["features"]),
    }
    (RAW / "natural-earth-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
