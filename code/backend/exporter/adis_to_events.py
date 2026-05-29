#!/usr/bin/env python3
"""Transform an ADIS outbreak CSV into a CSV matching the `events` schema.

Source: semicolon-delimited ADIS (Animal Disease Information System) export.
Target: columns of the `events` table defined in schema.md, minus the
database-managed columns (`id`, `created_at`, `updated_at`).

Usage:
    python adis_to_events.py input.csv output.csv
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

# Reference point used by the schema for `distance_km` (Bern, Switzerland).
BERN_LAT = 46.9480
BERN_LON = 7.4474

# Output columns, in order. Database-managed columns are omitted; the
# `priority` and `relevance_score` columns are emitted blank because the
# schema marks them nullable and no derivation rule is specified upstream.
EVENT_COLUMNS = [
    "disease",
    "subtype",
    "species",
    "population",
    "source",
    "external_id",
    "occurred_at",
    "admin_level_1",
    "admin_level_2",
    "admin_level_3",
    "latitude",
    "longitude",
    "cases",
    "deaths",
    "susceptible",
    "distance_km",
    "relevance_score",
    "priority",
]


# ---------- field-level helpers ----------

def clean_str(value) -> str | None:
    """Return a trimmed string or None for NaN/empty values."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    s = str(value).strip()
    return s or None


def parse_decimal(value) -> float | None:
    """Parse a decimal that may use comma as the decimal separator."""
    s = clean_str(value)
    if s is None:
        return None
    # ADIS uses comma as decimal separator (e.g. "46,9480").
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_uint(value) -> int | None:
    """Parse a non-negative integer; return None for missing/invalid."""
    s = clean_str(value)
    if s is None:
        return None
    try:
        n = int(float(s))
    except ValueError:
        return None
    return n if n >= 0 else None


def haversine_km(lat1, lon1, lat2, lon2) -> float | None:
    """Great-circle distance in kilometres between two WGS84 points."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    r = 6371.0088  # mean Earth radius, km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ---------- row-level mappings ----------

def derive_population(row) -> str | None:
    """Infer the `population` field from ADIS columns.

    - Wildlife type "Wild"      -> "wild"
    - Production Type present   -> "poultry"   (ADIS livestock/poultry records)
    - Epidemiological unit Apiary -> "apiary"
    - Captive wildlife          -> "captive"
    """
    wildlife = clean_str(row.get("Wildlife type 1"))
    production = clean_str(row.get("Production Type 1"))
    epi_unit = clean_str(row.get("Epidemiological unit"))

    if wildlife:
        wl = wildlife.lower()
        if wl == "wild":
            return "wild"
        if wl in ("captive", "captive wild"):
            return "captive"
    if production:
        return "poultry"
    if epi_unit and epi_unit.lower() == "apiary":
        return "apiary"
    return None


def derive_occurred_at(row) -> str | None:
    """Prefer Confirmation date; fall back to Suspicion/Start date."""
    for col in ("Confirmation date", "Suspicion/Start date", "Submitted on"):
        val = clean_str(row.get(col))
        if val:
            return val
    return None


def map_row(row) -> dict:
    lat = parse_decimal(row.get("Latitude"))
    lon = parse_decimal(row.get("Longitude"))
    dist = haversine_km(lat, lon, BERN_LAT, BERN_LON)

    return {
        "disease": clean_str(row.get("Disease name")),
        "subtype": clean_str(row.get("Disease type")),
        "species": clean_str(row.get("Species 1")),
        "population": derive_population(row),
        "source": "adis",
        "external_id": clean_str(row.get("Reference")),
        "occurred_at": derive_occurred_at(row),
        "admin_level_1": clean_str(row.get("Administrative division level 1")),
        "admin_level_2": clean_str(row.get("Administrative division level 2")),
        "admin_level_3": clean_str(row.get("Administrative division level 3")),
        "latitude": round(lat, 6) if lat is not None else None,
        "longitude": round(lon, 6) if lon is not None else None,
        "cases": parse_uint(row.get("Cases 1")),
        "deaths": parse_uint(row.get("Dead 1")),
        "susceptible": parse_uint(row.get("Susceptible 1")),
        "distance_km": round(dist, 2) if dist is not None else None,
        "relevance_score": None,
        "priority": None,
    }


# ---------- entry point ----------

def transform(input_path: Path, output_path: Path) -> int:
    df = pd.read_csv(input_path, sep=";", dtype=str)
    records = [map_row(row) for _, row in df.iterrows()]
    out = pd.DataFrame.from_records(records, columns=EVENT_COLUMNS)
    out.to_csv(output_path, index=False)
    return len(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="Path to ADIS source CSV")
    ap.add_argument("output", type=Path, help="Path to write events CSV")
    args = ap.parse_args()

    n = transform(args.input, args.output)
    print(f"Wrote {n} events to {args.output}")


if __name__ == "__main__":
    main()
