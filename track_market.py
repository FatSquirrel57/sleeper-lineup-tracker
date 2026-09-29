import csv
import json
import os
import requests
from datetime import datetime, timezone

OUTPUT_FILE = "sleeper_market_history.csv"
PLAYER_FILE = "sleeper_players.json"

TRENDING_LIMIT = 100

# For our high-frequency market tape, we're tracking the rolling 1-hour market.
WINDOWS = [1]


def load_players():
    if not os.path.exists(PLAYER_FILE):
        raise FileNotFoundError(
            f"{PLAYER_FILE} does not exist. Run update_players.py first."
        )

    with open(PLAYER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["players"]


def get_trending(trend_type, hours):
    url = f"https://api.sleeper.app/v1/players/nfl/trending/{trend_type}"

    params = {
        "lookback_hours": hours,
        "limit": TRENDING_LIMIT,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    return response.json()


def get_player_name(player):
    full_name = player.get("full_name")

    if full_name:
        return full_name

    first_name = player.get("first_name", "")
    last_name = player.get("last_name", "")

    return f"{first_name} {last_name}".strip()


def collect_market_data(players):
    timestamp = datetime.now(timezone.utc).isoformat()

    rows = []

    for trend_type in ["add", "drop"]:
        for hours in WINDOWS:

            data = get_trending(trend_type, hours)

            for rank, trending_player in enumerate(data, start=1):

                player_id = str(trending_player["player_id"])
                player = players.get(player_id, {})

                rows.append({
                    "timestamp_utc": timestamp,
                    "trend_type": trend_type,
                    "lookback_hours": hours,
                    "rank": rank,
                    "player_id": player_id,
                    "player_name": get_player_name(player),
                    "position": player.get("position", ""),
                    "team": player.get("team", ""),
                    "count": trending_player["count"],
                })

    return rows


def save_rows(rows):

    fieldnames = [
        "timestamp_utc",
        "trend_type",
        "lookback_hours",
        "rank",
        "player_id",
        "player_name",
        "position",
        "team",
        "count",
    ]

    file_exists = os.path.exists(OUTPUT_FILE)

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)


if __name__ == "__main__":

    players = load_players()

    rows = collect_market_data(players)
    save_rows(rows)

    print(f"Saved {len(rows)} market observations.")
