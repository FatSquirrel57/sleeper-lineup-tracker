import json
import requests
from datetime import datetime, timezone

PLAYERS_URL = "https://api.sleeper.app/v1/players/nfl"
OUTPUT_FILE = "sleeper_players.json"


def update_players():
    print("Downloading Sleeper NFL player database...")

    response = requests.get(PLAYERS_URL, timeout=60)
    response.raise_for_status()

    players = response.json()

    output = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "players": players,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f)

    print(f"Saved metadata for {len(players):,} players.")


if __name__ == "__main__":
    update_players()
