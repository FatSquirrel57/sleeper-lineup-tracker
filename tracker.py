import csv
import json
import os
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

LEAGUE_ID = "1312179819819053056"
STATE_FILE = "current_state.json"
LOG_FILE = "lineup_changes.csv"


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


def get_players():
    return get_json(
        "https://api.sleeper.app/v1/players/nfl"
    )


def build_snapshot(league, rosters, users):
    user_names = {
        user["user_id"]: user["display_name"]
        for user in users
    }

    roster_positions = league["roster_positions"]

    snapshot = {
        "timestamp": datetime.now(
            ZoneInfo("America/New_York")
        ).strftime("%Y-%m-%d %I:%M:%S %p %Z"),
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


def load_previous_snapshot():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r") as file:
        return json.load(file)


def get_player_location(roster_data, player_id):
    if player_id in roster_data["starters"]:
        return roster_data["starters"][player_id]

    if player_id in roster_data["bench"]:
        return "BENCH"

    return None

def classify_movement(old_location, new_location):
    if old_location == "BENCH" and new_location != "BENCH":
        return "STARTED"

    if old_location != "BENCH" and new_location == "BENCH":
        return "BENCHED"

    return "SLOT_CHANGE"

def detect_changes(old_snapshot, new_snapshot):
    changes = []

    if old_snapshot is None:
        return changes

    for roster_id, new_roster in new_snapshot["rosters"].items():

        old_roster = old_snapshot["rosters"].get(roster_id)

        if old_roster is None:
            continue

        all_player_ids = set()

        all_player_ids.update(old_roster["starters"].keys())
        all_player_ids.update(old_roster["bench"])
        all_player_ids.update(new_roster["starters"].keys())
        all_player_ids.update(new_roster["bench"])

        for player_id in all_player_ids:
            old_location = get_player_location(old_roster, player_id)
            new_location = get_player_location(new_roster, player_id)

            # Only track lineup movement.
            # Ignore adds/drops for now.
            if (
                old_location is not None
                and new_location is not None
                and old_location != new_location
            ):
                changes.append({
                    "timestamp": new_snapshot["timestamp"],
                    "roster_id": roster_id,
                    "manager": new_roster["owner_name"],
                    "player_id": player_id,
                    "from": old_location,
                    "to": new_location,
                    "movement": classify_movement(
                        old_location,
                        new_location
                    )
                })

    return changes


def add_player_names(changes, players):
    for change in changes:
        player = players.get(change["player_id"], {})

        full_name = player.get("full_name")

        if not full_name:
            first = player.get("first_name", "")
            last = player.get("last_name", "")
            full_name = f"{first} {last}".strip()

        change["player_name"] = full_name or "Unknown"


def write_changes(changes):
    if not changes:
        print("No lineup changes detected.")
        return

    file_exists = os.path.exists(LOG_FILE)

    with open(LOG_FILE, "a", newline="") as file:
        fieldnames = [
            "timestamp",
            "manager",
            "player_name",
            "player_id",
            "from",
            "to",
            "movement",
            "roster_id"
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for change in changes:
            writer.writerow(change)

    print(f"Recorded {len(changes)} lineup change(s).")


def save_snapshot(snapshot):
    with open(STATE_FILE, "w") as file:
        json.dump(snapshot, file, indent=2)


def main():
    league = get_league()
    rosters = get_rosters()
    users = get_users()

    old_snapshot = load_previous_snapshot()
    new_snapshot = build_snapshot(league, rosters, users)

    changes = detect_changes(old_snapshot, new_snapshot)

    if changes:
        players = get_players()
        add_player_names(changes, players)

        for change in changes:
            print(
                f"{change['manager']}: "
                f"{change['player_name']} "
                f"{change['from']} -> {change['to']}"
            )

    write_changes(changes)
    save_snapshot(new_snapshot)


if __name__ == "__main__":
    main()
