"""Build compact chart data for the full story from frozen local research inputs.

No network calls, pandas dependency, or manual edits to game counts. Run from
any directory with `python scripts/build_data.py`. Raw inputs stay out of Git.
"""

import csv
import hashlib
import json
import math
import unicodedata
from collections import defaultdict
from pathlib import Path

from story_data import build_story
from build_player_tree import build_player_tree

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research" / "validation-data"
OUT = ROOT / "data"

ALIASES = {
    "usa": "US", "uk": "GB", "england": "GB", "scotland": "GB",
    "wales": "GB", "great britain": "GB", "northern ireland": "GB",
    "the netherlands": "NL", "netherlands": "NL", "cape verde": "CV",
    "czech republic": "CZ", "czechia": "CZ", "south korea": "KR",
    "uae": "AE", "turkey": "TR",
}


def normalise(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    ).strip()


def rows(name: str):
    with (RAW / name).open(newline="", encoding="utf-8-sig") as source:
        yield from csv.DictReader(source)


def write_json(name: str, value: object) -> int:
    OUT.mkdir(exist_ok=True)
    target = OUT / name
    target.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2 if name == "metadata.json" else None, separators=None if name == "metadata.json" else (",", ":")) + "\n",
        encoding="utf-8",
    )
    return target.stat().st_size


def country_codes() -> dict[str, str]:
    codes = dict(ALIASES)
    with (RAW / "countryInfo.txt").open(encoding="utf-8") as source:
        for record in csv.reader((line for line in source if not line.startswith("#")), delimiter="\t"):
            if len(record) >= 5:
                codes[normalise(record[4])] = record[0]
    return codes


def optional_number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None


def included_games() -> dict[int, dict]:
    result = {}
    for game in rows("game.csv"):
        try:
            identifier = int(game["id_bgg"])
            year = int(float(game["yearpublished"]))
            rating_votes = int(float(game["usersrated"]))
            complexity_votes = int(float(game["numweights"]))
            rating = float(game["average"])
            complexity = float(game["averageweight"])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if (
            game["game_type"] == "boardgame"
            and 1900 <= year <= 2024
            and rating_votes >= 1000
            and complexity_votes >= 30
            and 1 <= rating <= 10
            and 1 <= complexity <= 5
        ):
            assert identifier not in result, f"Duplicate qualifying game ID: {identifier}"
            result[identifier] = {
                "id": identifier, "title": game["name_game"], "year": year,
                "rating": rating, "rating_votes": rating_votes,
                "complexity": complexity, "complexity_votes": complexity_votes,
                "minutes": optional_number(game.get("playingtime")),
                "min_players": optional_number(game.get("min_player")), "max_players": optional_number(game.get("max_player")),
            }
    assert len(result) == 3964, f"Source cohort changed: {len(result)}"
    return result


def country_links(games: dict[int, dict], codes: dict[str, str]):
    labels = {int(item["id_family"]): item["family"][len("Country: "):]
              for item in rows("family.csv") if item["family"].startswith("Country: ")}
    links = defaultdict(set)
    unrecognised = defaultdict(set)
    country_tagged = set()
    for bridge in rows("b_game_family.csv"):
        game_id = int(bridge["id_bgg"])
        label = labels.get(int(bridge["id_family"]))
        if game_id not in games or label is None:
            continue
        country_tagged.add(game_id)
        iso = codes.get(normalise(label))
        if iso:
            links[iso].add(game_id)
        else:
            unrecognised[label].add(game_id)
    assert len(country_tagged) == 762, len(country_tagged)
    assert len(set().union(*links.values())) == 750
    assert len(links) == 98
    return links, unrecognised


def shape_data():
    geometry = json.loads((RAW / "natural-earth-countries.geojson").read_text(encoding="utf-8"))
    features = []
    points = {}
    for feature in geometry["features"]:
        properties = feature["properties"]
        # Natural Earth's primary ISO_A2 is -99 for a few valid places;
        # its explicit ISO_A2_EH supplies those codes without name matching.
        iso = properties["ISO_A2"]
        if not (len(iso) == 2 and iso.isalpha()):
            iso = properties.get("ISO_A2_EH", iso)
        label_x, label_y = properties.get("LABEL_X"), properties.get("LABEL_Y")
        if len(iso) == 2 and iso.isalpha() and label_x is not None and label_y is not None:
            points[iso] = (float(label_x), float(label_y))
        features.append({
            "type": "Feature",
            "properties": {"iso": iso, "name": properties["NAME"]},
            "geometry": feature["geometry"],
        })
    return {"type": "FeatureCollection", "features": features}, points


def fingerprint(name):
    with (RAW / name).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def main() -> None:
    games = included_games()
    links, unrecognised = country_links(games, country_codes())
    world, points = shape_data()
    country_names = {}
    with (RAW / "countryInfo.txt").open(encoding="utf-8") as source:
        for record in csv.reader((line for line in source if not line.startswith("#")), delimiter="\t"):
            if len(record) >= 5:
                country_names[record[0]] = record[4]
    country_names.update({"US": "United States", "GB": "United Kingdom"})
    countries = []
    for iso, ids in links.items():
        location = points.get(iso)
        # Stable examples: the three games with the most community ratings.
        examples = [games[game_id]["title"] for game_id in sorted(
            ids, key=lambda game_id: (-games[game_id]["rating_votes"],
                                      games[game_id]["title"])
        )[:3]]
        countries.append({
            "iso": iso,
            "country": country_names.get(iso, iso),
            "game_count": len(ids),
            "longitude": location[0] if location else None,
            "latitude": location[1] if location else None,
            "examples": examples,
            "example_titles": ", ".join(examples),
        })
    countries.sort(key=lambda item: (-item["game_count"], item["country"]))
    mapped = [item for item in countries if item["longitude"] is not None]
    assert len(countries) == 98 and sum(item["game_count"] for item in countries) >= 750
    assert all(-180 <= item["longitude"] <= 180 and -90 <= item["latitude"] <= 90 for item in mapped)
    story = build_story(games, links, countries, RAW, country_codes(), normalise)
    story["player_tree.json"] = build_player_tree(story["games.json"])
    sizes = {
        "countries.json": write_json("countries.json", countries),
        "world.geojson": write_json("world.geojson", world),
    }
    sizes.update({name: write_json(name, value) for name, value in story.items()})
    source_manifest = json.loads((RAW / "natural-earth-manifest.json").read_text(encoding="utf-8"))
    meta = {
        "updated": "2026-10-23",
        "pipeline_version": 4,
        "input_sha256": {name: fingerprint(name)
                         for name in ["game.csv", "family.csv", "b_game_family.csv", "category.csv", "b_game_category.csv", "mechanic.csv", "b_game_mechanic.csv", "countryInfo.txt", "cities15000.zip"]},
        "statistics_vintage": "Mixed: the source adds games without refreshing existing statistics; release date is not the date of every rating.",
        "source_release": "2026-09-22", "source_acquired": "2026-10-05",
        "story_games": len(story["games.json"]), "city_locations": len(story["cities.json"]),
        "files": sizes.copy(),
        "cohort": "BGG base games released 1900–2024 with at least 1,000 ratings and 30 complexity votes, valid rating and complexity, and an explicit Country: or Cities: family tag",
        "qualifying_games": len(games),
        "country_tagged_games": 762,
        "country_geocoded_games": len(set().union(*links.values())),
        "country_associations": len(countries),
        "countries_with_shape_point": len(mapped),
        "countries_without_shape_point": [item["iso"] for item in countries if item["longitude"] is None],
        "unmatched_historical_or_ambiguous_tags": sorted(unrecognised),
        "sources": {
            "boardgames": "https://www.kaggle.com/datasets/sylvainballerini/bgg-data-full",
            "geonames": "https://www.geonames.org/export/",
            "boundaries": source_manifest,
        },
        "note": "Counts are documented game-country associations, not sales, production locations or a complete setting census. One game can belong to several countries.",
        "output_bytes_excluding_metadata": sum(sizes.values()),
    }
    sizes["metadata.json"] = write_json("metadata.json", meta)
    print(json.dumps({"files": sizes, "countries": len(countries), "mappable": len(mapped),
                      "missing_geometry": meta["countries_without_shape_point"]}, indent=2))


if __name__ == "__main__":
    main()
