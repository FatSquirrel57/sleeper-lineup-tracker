import csv
from collections import defaultdict
from datetime import datetime

INPUT_FILE = "sleeper_market_history.csv"
OUTPUT_FILE = "sleeper_market_current.csv"


def load_history():
    rows = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            row["rank"] = int(row["rank"])
            row["count"] = int(row["count"])
            row["timestamp_dt"] = datetime.fromisoformat(row["timestamp_utc"])

            rows.append(row)

    return rows


def analyze_market(rows):

    # Group observations by add/drop + player.
    history = defaultdict(list)

    for row in rows:
        key = (
            row["trend_type"],
            row["player_id"],
        )

        history[key].append(row)

    output = []

    for (trend_type, player_id), observations in history.items():

        # Sort oldest -> newest
        observations.sort(key=lambda x: x["timestamp_dt"])

        current = observations[-1]

        # Only include players appearing in the newest overall snapshot
        latest_timestamp = max(row["timestamp_dt"] for row in rows)

        if current["timestamp_dt"] != latest_timestamp:
            continue

        previous = observations[-2] if len(observations) >= 2 else None

        if previous:
            minutes_elapsed = (
                current["timestamp_dt"] - previous["timestamp_dt"]
            ).total_seconds() / 60

            rank_change = previous["rank"] - current["rank"]
            count_change = current["count"] - previous["count"]

            if minutes_elapsed > 0:
                count_velocity_per_hour = (
                    count_change / minutes_elapsed
                ) * 60
            else:
                count_velocity_per_hour = 0

        else:
            minutes_elapsed = ""
            rank_change = ""
            count_change = ""
            count_velocity_per_hour = ""

        output.append({
            "trend_type": trend_type,
            "player_id": player_id,
            "player_name": current["player_name"],
            "position": current["position"],
            "team": current["team"],
            "current_rank": current["rank"],
            "current_count": current["count"],
            "previous_rank": previous["rank"] if previous else "",
            "previous_count": previous["count"] if previous else "",
            "minutes_elapsed": (
                round(minutes_elapsed, 2)
                if minutes_elapsed != ""
                else ""
            ),
            "rank_change": rank_change,
            "count_change": count_change,
            "count_velocity_per_hour": (
                round(count_velocity_per_hour, 2)
                if count_velocity_per_hour != ""
                else ""
            ),
            "timestamp_utc": current["timestamp_utc"],
        })

    return output


def save_analysis(rows):

    fieldnames = [
        "trend_type",
        "player_id",
        "player_name",
        "position",
        "team",
        "current_rank",
        "current_count",
        "previous_rank",
        "previous_count",
        "minutes_elapsed",
        "rank_change",
        "count_change",
        "count_velocity_per_hour",
        "timestamp_utc",
    ]

    # Put adds first, then drops.
    # Within each group, rank #1 appears first.
    rows.sort(
        key=lambda x: (
            0 if x["trend_type"] == "add" else 1,
            x["current_rank"],
        )
    )

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":

    rows = load_history()
    analysis = analyze_market(rows)
    save_analysis(analysis)

    print(f"Analyzed {len(analysis)} current market players.")
