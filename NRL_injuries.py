import os
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Get today's date
today_date = datetime.today().strftime("%Y-%m-%d")

# Directories for storing injury reports
main_folder = "nrl_injuries"
os.makedirs(main_folder, exist_ok=True)

# Create a folder for today's date
folder_name = os.path.join(main_folder, f"nrl_injuries_{today_date}")
os.makedirs(folder_name, exist_ok=True)

# File paths
json_filename = os.path.join(folder_name, "injury_report.json")
csv_filename = os.path.join(folder_name, "injury_report.csv")
log_filename = os.path.join(folder_name, "scraper.log")
latest_folder = os.path.join(main_folder, "latest")
os.makedirs(latest_folder, exist_ok=True)
latest_json_filename = os.path.join(latest_folder, "nrl_injuries_latest.json")
latest_csv_filename = os.path.join(latest_folder, "nrl_injuries_latest.csv")

# URL for NRL injury list
url = "https://www.zerotackle.com/nrl/injuries-suspensions/"

# Track log messages
log_messages = []
injury_list = []

def scrape_nrl_injuries():
    """Scrape injury data from the NRL website (Zero Tackle)."""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        if response.status_code != 200:
            log_messages.append(f"❌ Failed to fetch NRL injury data (Status: {response.status_code})")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Finding tables containing injury data
        tables = soup.find_all('table', class_='table')
        
        if not tables:
            log_messages.append("❌ No injury tables found on the page")
            return
        
        # Process each table
        for table in tables:
            rows = table.find_all('tr')
            team_name = "Unknown"
            
            for row in rows:
                cols = row.find_all('td')
                
                # Team name row (found in <h4>)
                if len(cols) == 0:
                    team_name_tag = table.find_previous('h4')
                    team_name = team_name_tag.get_text(strip=True) if team_name_tag else "Unknown Team"
                    log_messages.append(f"✅ Processing team: {team_name}")
                
                # Player injury row
                elif len(cols) >= 3:
                    player = cols[1].text.strip()  # Player name is in the second column
                    injury_type = cols[2].text.strip()  # Injury reason is in the third column
                    return_date = cols[3].text.strip()  # Expected return is in the fourth column
                    
                    # Generate a unique ID for the injury
                    injury_id = f"{team_name.lower().replace(' ', '_')}_{player.lower().replace(' ', '_')}"

                    injury_list.append({
                        "Player Name": player,
                        "Athlete ID": "N/A",  # NRL doesn't provide athlete IDs
                        "Team": team_name,
                        "Injury ID": injury_id,
                        "Status": "Injured",  # Default status
                        "Injury Type": injury_type,
                        "Return Date": return_date,
                        "Short Comment": "",
                        "Long Comment": "",
                        "Reported Date": today_date
                    })
        
        log_messages.append(f"✅ Total injuries found: {len(injury_list)}")
        
    except Exception as e:
        log_messages.append(f"❌ Error scraping NRL injury data: {str(e)}")

def main():
    scrape_nrl_injuries()
    
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
    main()
