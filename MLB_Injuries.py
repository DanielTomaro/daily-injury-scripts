import os
import aiohttp
import asyncio
import json
import pandas as pd
from datetime import datetime

# Get today's date
today_date = datetime.today().strftime("%Y-%m-%d")

# Directories for storing injury reports
main_folder = "mlb_injuries"
os.makedirs(main_folder, exist_ok=True)

# Create a folder for today's date
folder_name = os.path.join(main_folder, f"mlb_injuries_{today_date}")
os.makedirs(folder_name, exist_ok=True)

# File paths
json_filename = os.path.join(folder_name, "injury_report.json")
csv_filename = os.path.join(folder_name, "injury_report.csv")
log_filename = os.path.join(folder_name, "scraper.log")
latest_folder = os.path.join(main_folder, "latest")
os.makedirs(latest_folder, exist_ok=True)
latest_json_filename = os.path.join(latest_folder, "mlb_injuries_latest.json")
latest_csv_filename = os.path.join(latest_folder, "mlb_injuries_latest.csv")

# ESPN API base URL for injuries
base_url = "https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb/teams/{}/injuries"

# ESPN Team IDs for MLB teams
team_ids = {
    "Arizona Diamondbacks": 29, "Atlanta Braves": 15, "Baltimore Orioles": 1, "Boston Red Sox": 2,
    "Chicago Cubs": 16, "Chicago White Sox": 4, "Cincinnati Reds": 17, "Cleveland Guardians": 5,
    "Colorado Rockies": 27, "Detroit Tigers": 6, "Houston Astros": 18, "Kansas City Royals": 7,
    "Los Angeles Angels": 3, "Los Angeles Dodgers": 19, "Miami Marlins": 28, "Milwaukee Brewers": 8,
    "Minnesota Twins": 9, "New York Mets": 21, "New York Yankees": 10, "Oakland Athletics": 11,
    "Philadelphia Phillies": 22, "Pittsburgh Pirates": 23, "San Diego Padres": 25, "San Francisco Giants": 26,
    "Seattle Mariners": 12, "St. Louis Cardinals": 24, "Tampa Bay Rays": 30, "Texas Rangers": 13,
    "Toronto Blue Jays": 14, "Washington Nationals": 20
}

# Player IDs file (MLB)
players_file = "player_ids/MLB_Players.csv"

# Load player data to map Athlete ID to Player Name
if os.path.exists(players_file):
    players_df = pd.read_csv(players_file, dtype={"Athlete ID": str})
else:
    players_df = pd.DataFrame(columns=["Athlete ID", "Player Name"])

# Track log messages
log_messages = []
injury_list = []

async def fetch_json(session, url):
    """Helper function to fetch JSON data from a URL."""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                log_messages.append(f"❌ Failed to fetch {url} (Status: {response.status})")
    except Exception as e:
        log_messages.append(f"❌ Error fetching {url} - {e}")
    return None

async def fetch_injury_details(session, ref_urls):
    """Fetch full injury details from the given reference URLs."""
    tasks = [fetch_json(session, url["$ref"]) for url in ref_urls]
    return await asyncio.gather(*tasks)

async def fetch_injury_data(session, team, team_id):
    """Fetch injury list for a team and retrieve full injury details."""
    url = base_url.format(team_id)
    team_data = await fetch_json(session, url)
    
    if team_data and "items" in team_data:
        detailed_injuries = await fetch_injury_details(session, team_data["items"])
        
        for injury in detailed_injuries:
            if injury:
                # Extract and clean Athlete ID
                raw_athlete_id = injury.get("athlete", {}).get("$ref", "").split("/")[-1]
                athlete_id = raw_athlete_id.split("?")[0]  # Remove any query parameters
                
                # Ensure both ID formats match (convert to string)
                athlete_id = str(athlete_id)
                players_df["Athlete ID"] = players_df["Athlete ID"].astype(str)

                # Attempt to find the Player Name
                player_name = players_df.loc[players_df["Athlete ID"] == athlete_id, "Player Name"].values
                player_name = player_name[0] if len(player_name) > 0 else "Unknown"

                injury_list.append({
                    "Player Name": player_name,
                    "Athlete ID": athlete_id,
                    "Team": team,
                    "Injury ID": injury.get("id"),
                    "Status": injury.get("status"),
                    "Injury Type": injury.get("details", {}).get("type", "Unknown"),
                    "Return Date": injury.get("details", {}).get("returnDate", "Unknown"),
                    "Short Comment": injury.get("shortComment", ""),
                    "Long Comment": injury.get("longComment", ""),
                    "Reported Date": injury.get("date", "")
                })
        log_messages.append(f"✅ {team}: Retrieved {len(detailed_injuries)} injury records.")
    else:
        log_messages.append(f"⚠️ {team}: No injuries found.")

async def get_injury_reports():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_injury_data(session, team, team_id) for team, team_id in team_ids.items()]
        await asyncio.gather(*tasks)

async def main():
    await get_injury_reports()
    
    # Save JSON results
    with open(json_filename, "w") as json_file:
        json.dump(injury_list, json_file, indent=4)
    with open(latest_json_filename, "w") as json_file:
        json.dump(injury_list, json_file, indent=4)
    
    # Convert to DataFrame and save as CSV
    df = pd.DataFrame(injury_list)
    df.to_csv(csv_filename, index=False)
    df.to_csv(latest_csv_filename, index=False)
    
    # Save log file
    with open(log_filename, "w") as log_file:
        log_file.write("\n".join(log_messages))

    print(f"✅ Scraper completed. Data saved in {folder_name}. Check {log_filename} for details.")

if __name__ == "__main__":
    asyncio.run(main())
