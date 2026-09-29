import json
import urllib.request

LEAGUE_ID = "1312179819819053056"

def get_json(url):

    """Retrieve JSON data from Sleeper's API."""
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())

def get_league():

    url = f"https://api.sleeper.app/v1/league/{LEAGUE_ID}"
    return get_json(url)

def get_rosters():

    url = f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/rosters"
    return get_json(url)

def get_users():

    url = f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/users"
    return get_json(url)

def main():

    league = get_league()
    rosters = get_rosters()
    users = get_users()
  
    print(f"League: {league['name']}")
    print(f"Season: {league['season']}")
    print(f"Teams: {len(rosters)}")
    print()
  
    print("Roster positions:")
    print(league["roster_positions"])
    print()
  
    print("League members:")
    for user in users:
        print(f"- {user['display_name']} ({user['user_id']})")

if __name__ == "__main__":
    main()
