import json
import urllib.request
from datetime import datetime, timezone

LEAGUE_ID = "1312179819819053056"
STATE_FILE = "current_state.json"


def get_json(url):
    """Retrieve JSON data from Sleeper's API."""
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())


def get_league():
    return get_json(
        f"https://api.sleeper.app/v1/league/{LEAGUE_ID}"
    )


def get_rosters():
    return get_json(
        f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/rosters"
    )


def get_users():
    return get_json(
        f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/users"
    )


def build_snapshot(league, rosters, users):
    # Connect Sleeper user IDs to display names
    user_names = {
        user["user_id"]: user["display_name"]
        for user in users
    }

    roster_positions = league["roster_positions"]

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "league_id": LEAGUE_ID,
        "rosters": {}
    }

    for roster in rosters:
        roster_id = str(roster["roster_id"])
        owner_id = roster.get("owner_id")
        owner_name = user_names.get(owner_id, "Unknown")

        starters = roster.get("starters", [])
        all_players = roster.get("players", []) or []

        starter_slots = {}

        for index, player_id in enumerate(starters):
            if index < len(roster_positions):
                slot = roster_positions[index]
            else:
                slot = "UNKNOWN"

            starter_slots[player_id] = slot

        bench_players = [
            player_id
            for player_id in all_players
            if player_id not in starters
        ]

        snapshot["rosters"][roster_id] = {
            "owner_id": owner_id,
            "owner_name": owner_name,
            "starters": starter_slots,
            "bench": bench_players
        }

    return snapshot


def main():
    league = get_league()
    rosters = get_rosters()
    users = get_users()

    snapshot = build_snapshot(league, rosters, users)

    with open(STATE_FILE, "w") as file:
        json.dump(snapshot, file, indent=2)

    print(f"League: {league['name']}")
    print(f"Saved snapshot for {len(rosters)} teams.")
    print(f"Snapshot time: {snapshot['timestamp']}")


if __name__ == "__main__":
    main()
