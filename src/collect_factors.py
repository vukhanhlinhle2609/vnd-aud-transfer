"""Collect public market factors used by the AUD/VND forecast.

The Federal Reserve and RBA feeds need no API keys.  Each successful run
rebuilds a compact daily file; if an individual source is temporarily
unavailable, the previous values for that column are preserved.
"""

from __future__ import annotations

import csv
import subprocess
from datetime import date, datetime
from functools import lru_cache
from io import StringIO
from pathlib import Path

import requests


START_DATE = date(2024, 1, 1)
ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "data" / "market_factors.csv"

FRED_SERIES = {
    "aud_usd": "DEXUSAL",
    "broad_usd": "DTWEXBGS",
    "usd_cny": "DEXCHUS",
    "vix": "VIXCLS",
    "brent_oil": "DCOILBRENTEU",
    "us_10y": "DGS10",
    "sp500": "SP500",
}

RBA_SERIES = {
    "rba_aud_usd": (
        "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv",
        "FXRUSD",
    ),
    "rba_aud_twi": (
        "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv",
        "FXRTWI",
    ),
    "rba_aud_cny": (
        "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv",
        "FXRCR",
    ),
    "rba_aud_vnd": (
        "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv",
        "FXRVD",
    ),
    "rba_aud_jpy": (
        "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv",
        "FXRJY",
    ),
    "rba_aud_eur": (
        "https://www.rba.gov.au/statistics/tables/csv/f11.1-data.csv",
        "FXREUR",
    ),
    "rba_cash_rate": (
        "https://www.rba.gov.au/statistics/tables/csv/f1-data.csv",
        "FIRMMCRTD",
    ),
    "au_10y": (
        "https://www.rba.gov.au/statistics/tables/csv/f2-data.csv",
        "FCMYGBAG10D",
    ),
}


@lru_cache(maxsize=None)
def fetch_text(url: str) -> str:
    try:
        completed = subprocess.run(
            [
                "curl",
                "-L",
                "--fail",
                "--silent",
                "--show-error",
                "--max-time",
                "60",
                url,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=70,
        )
        return completed.stdout.lstrip("\ufeff")
    except (FileNotFoundError, subprocess.SubprocessError):
        response = requests.get(
            url,
            timeout=45,
            headers={"User-Agent": "vnd-aud-transfer-dashboard/1.0"},
        )
        response.raise_for_status()
        return response.text.lstrip("\ufeff")


def fetch_fred(series_id: str) -> dict[str, float]:
    url = (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}&cosd={START_DATE.isoformat()}"
    )
    observations: dict[str, float] = {}
    for row in csv.DictReader(StringIO(fetch_text(url))):
        raw_value = row.get(series_id, "")
        if not raw_value or raw_value == ".":
            continue
        observations[row["observation_date"]] = float(raw_value)
    return observations


def fetch_rba(url: str, series_id: str) -> dict[str, float]:
    table = list(csv.reader(StringIO(fetch_text(url))))
    series_row = next(row for row in table if row and row[0] == "Series ID")
    value_index = series_row.index(series_id)
    observations: dict[str, float] = {}
    for row in table:
        if len(row) <= value_index or not row[value_index]:
            continue
        try:
            observation_date = datetime.strptime(row[0], "%d-%b-%Y").date()
            value = float(row[value_index])
        except (ValueError, TypeError):
            continue
        if observation_date >= START_DATE:
            observations[observation_date.isoformat()] = value
    return observations


def read_existing() -> dict[str, dict[str, float]]:
    existing = {name: {} for name in (*FRED_SERIES, *RBA_SERIES)}
    if not OUTPUT_FILE.exists():
        return existing
    with OUTPUT_FILE.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            observation_date = row.get("date", "")
            for name in existing:
                raw_value = row.get(name, "")
                if raw_value:
                    existing[name][observation_date] = float(raw_value)
    return existing


def main() -> None:
    series = read_existing()
    successful = 0

    for name, series_id in FRED_SERIES.items():
        try:
            downloaded = fetch_fred(series_id)
        except requests.RequestException as error:
            print(f"Keeping existing {name}: {error}")
            continue
        if downloaded:
            series[name] = downloaded
            successful += 1
            print(f"Downloaded {len(downloaded):,} {name} observations")

    for name, (url, series_id) in RBA_SERIES.items():
        try:
            downloaded = fetch_rba(url, series_id)
        except (requests.RequestException, StopIteration, ValueError) as error:
            print(f"Keeping existing {name}: {error}")
            continue
        if downloaded:
            series[name] = downloaded
            successful += 1
            print(f"Downloaded {len(downloaded):,} {name} observations")

    all_dates = sorted(
        {
            observation_date
            for observations in series.values()
            for observation_date in observations
        }
    )
    if not all_dates:
        raise RuntimeError("No market-factor observations are available")

    fieldnames = ["date", *series]
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for observation_date in all_dates:
            writer.writerow(
                {
                    "date": observation_date,
                    **{
                        name: observations.get(observation_date, "")
                        for name, observations in series.items()
                    },
                }
            )

    print(
        f"Saved {len(all_dates):,} dates and {len(series)} factors "
        f"({successful} feeds refreshed) to {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
