#!/usr/bin/env python3
"""Convert Google Takeout Maps reviews (JSON or GeoJSON) to the widget format."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


PLACE_KEYS = (
    "Luogo",
    "placeName",
    "locationName",
    "businessName",
    "title",
    "name",
    "location",
)
RATING_KEYS = ("Valutazione", "rating", "stars", "score")
REVIEW_KEYS = (
    "Recensione",
    "reviewText",
    "review",
    "comment",
    "text",
    "content",
    "description",
)
URL_KEYS = (
    "URL_GoogleMaps",
    "googleMapsUrl",
    "googleMapsURI",
    "googleMapsLink",
    "reviewUrl",
    "locationUrl",
    "url",
    "uri",
)
LATITUDE_KEYS = ("Latitudine", "latitude", "lat")
LONGITUDE_KEYS = ("Longitudine", "longitude", "lon", "lng")


def _key(value: str) -> str:
    """Normalize a JSON key so aliases tolerate spaces and punctuation."""
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _sources(record: dict[str, Any]) -> list[dict[str, Any]]:
    sources = [record]
    for key in ("properties", "attributes"):
        nested = record.get(key)
        if isinstance(nested, dict):
            sources.append(nested)
    location = record.get("location")
    if isinstance(location, dict):
        sources.append(location)
    return sources


def _find(record: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    wanted = {_key(alias) for alias in aliases}
    for source in _sources(record):
        for key, value in source.items():
            if _key(str(key)) in wanted and value not in (None, ""):
                return value
    return None


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, dict):
        for key in ("name", "title", "text", "value", "address"):
            nested = value.get(key)
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
    return ""


def _as_rating(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    match = re.search(r"\d+(?:[.,]\d+)?", str(value))
    if not match:
        return None
    try:
        rating = int(float(match.group().replace(",", ".")))
    except ValueError:
        return None
    return max(1, min(5, rating))


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if -180 <= number <= 180 else None


def _coordinates(record: dict[str, Any]) -> tuple[float, float] | None:
    for source in _sources(record):
        geometry = source.get("geometry")
        if isinstance(geometry, dict):
            coordinates = geometry.get("coordinates")
            # GeoJSON coordinate order is [longitude, latitude].
            if isinstance(coordinates, (list, tuple)) and len(coordinates) >= 2:
                longitude = _number(coordinates[0])
                latitude = _number(coordinates[1])
                if longitude is not None and latitude is not None and -90 <= latitude <= 90:
                    return latitude, longitude

        latitude = _number(_find(source, LATITUDE_KEYS))
        longitude = _number(_find(source, LONGITUDE_KEYS))
        if latitude is not None and longitude is not None and -90 <= latitude <= 90:
            return latitude, longitude

    return None


def _safe_maps_url(value: Any) -> str:
    url = _as_text(value)
    if not url:
        return ""
    try:
        parsed = urlsplit(url)
    except ValueError:
        return ""
    host = (parsed.hostname or "").casefold()
    trusted_host = host == "goo.gl" or host.endswith(".goo.gl") or host == "google.com" or host.endswith(".google.com") or host.endswith(".google.it")
    if parsed.scheme not in {"http", "https"} or not trusted_host:
        return ""
    return url


def _normalize_review(record: dict[str, Any]) -> dict[str, Any] | None:
    place = _as_text(_find(record, PLACE_KEYS))
    review = _as_text(_find(record, REVIEW_KEYS))
    rating = _as_rating(_find(record, RATING_KEYS))
    if not place or (not review and rating is None):
        return None

    result: dict[str, Any] = {
        "Luogo": place,
        "Valutazione": rating if rating is not None else 5,
        "Recensione": review,
        "URL_GoogleMaps": _safe_maps_url(_find(record, URL_KEYS)),
    }
    coordinates = _coordinates(record)
    if coordinates is not None:
        result["Latitudine"], result["Longitudine"] = coordinates
    return result


def _iter_reviews(value: Any):
    if isinstance(value, list):
        for item in value:
            yield from _iter_reviews(item)
        return
    if not isinstance(value, dict):
        return

    normalized = _normalize_review(value)
    if normalized is not None:
        yield normalized
        return

    for child in value.values():
        if isinstance(child, (dict, list)):
            yield from _iter_reviews(child)


def parse_takeout(input_path: Path) -> list[dict[str, Any]]:
    """Read a Takeout JSON/GeoJSON file and return widget-compatible reviews."""
    with input_path.open("r", encoding="utf-8-sig") as source_file:
        source_data = json.load(source_file)
    return list(_iter_reviews(source_data))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Converte recensioni Google Maps di Takeout in data.json per il widget."
    )
    parser.add_argument("input", type=Path, help="file JSON/GeoJSON esportato da Google Takeout")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("data.json"),
        help="file di destinazione (default: data.json)",
    )
    args = parser.parse_args(argv)

    try:
        reviews = parse_takeout(args.input)
        args.output.write_text(
            json.dumps(reviews, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, json.JSONDecodeError) as error:
        print(f"Errore: {error}", file=sys.stderr)
        return 1

    print(f"Esportate {len(reviews)} recensioni in {args.output}")
    if not reviews:
        print(
            "Attenzione: nessuna recensione riconosciuta. Verifica che il file contenga "
            "campi per luogo, valutazione o testo della recensione.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())