import requests
import pandas as pd
import os

# Define leagues and their ESPN API URLs
leagues = {
    "NBA": "https://sports.core.api.espn.com/v3/sports/basketball/nba/athletes?limit=5000",
    "NFL": "https://sports.core.api.espn.com/v3/sports/football/nfl/athletes?limit=5000",
    "MLB": "https://sports.core.api.espn.com/v3/sports/baseball/mlb/athletes?limit=5000",
    "NHL": "https://sports.core.api.espn.com/v3/sports/hockey/nhl/athletes?limit=5000",
}

# Create the folder if it doesn't exist
folder_name = "player_ids"
os.makedirs(folder_name, exist_ok=True)

# Loop through each league and fetch players
for league, url in leagues.items():
    response = requests.get(url)
    data = response.json()

    # Extract player info
    players = []
    for player in data.get("items", []):
        players.append({
            "Player Name": player.get("fullName", ""),
            "Athlete ID": player.get("id", "")
        })

    # Convert to DataFrame
    df = pd.DataFrame(players)

    # Save to CSV inside player_ids folder
    csv_filename = os.path.join(folder_name, f"{league}_Players.csv")
    df.to_csv(csv_filename, index=False)
    print(f"CSV file saved as {csv_filename}")

