import csv
import os
import requests
from datetime import datetime, timezone

OUTPUT_FILE = "sleeper_market_history.csv"

# How many trending players Sleeper should return
TRENDING_LIMIT = 100

# Lookback windows in hours
WINDOWS = [1, 6, 24]


def get_trending(trend_type, hours):
    url = f"https://api.sleeper.app/v1/players/nfl/trending/{trend_type}"

    params = {
        "lookback_hours": hours,
        "limit": TRENDING_LIMIT,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    return response.json()


def collect_market_data():
    timestamp = datetime.now(timezone.utc).isoformat()

    rows = []

    for trend_type in ["add", "drop"]:
        for hours in WINDOWS:

            data = get_trending(trend_type, hours)

            for rank, player in enumerate(data, start=1):
                rows.append({
                    "timestamp_utc": timestamp,
                    "trend_type": trend_type,
                    "lookback_hours": hours,
                    "rank": rank,
                    "player_id": player["player_id"],
                    "count": player["count"],
                })

    return rows


def save_rows(rows):

    fieldnames = [
        "timestamp_utc",
        "trend_type",
        "lookback_hours",
        "rank",
        "player_id",
        "count",
    ]

    file_exists = os.path.exists(OUTPUT_FILE)

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)


if __name__ == "__main__":

    rows = collect_market_data()
    save_rows(rows)

    print(f"Saved {len(rows)} market observations.")
