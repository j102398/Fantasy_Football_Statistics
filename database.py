import datetime
import requests
from bs4 import BeautifulSoup
import sqlite3

pageToScrape = requests.get('https://fbref.com/en/comps/9/Premier-League-Stats')
soup = BeautifulSoup(pageToScrape.text, "html.parser")

# Player info
players_used_elements = soup.find_all(attrs={"data-stat": "players_used"})
team_elements = soup.find_all(attrs={"data-stat": "team"})
nationality_elements = soup.find_all(attrs={"data-stat": "nationality"})
position_elements = soup.find_all(attrs={"data-stat": "position"})
age_elements = soup.find_all(attrs={"data-stat": "avg_age"})
possession_elements = soup.find_all(attrs={"data-stat": "possession"})
# Starts and minutes
games_elements = soup.find_all(attrs={"data-stat": "games"})
start_element = soup.find_all(attrs={"data-stat": "games_starts"})
minutes_elements = soup.find_all(attrs={"data-stat": "minutes"})
ninety_mins = soup.find_all(attrs={"data-stat": "minutes_90s"})

# G+A
goals_elements = soup.find_all(attrs={"data-stat": "goals"})
assist_elements = soup.find_all(attrs={"data-stat": "assists"})
goals_assists_elements = soup.find_all(attrs={"data-stat": "goals_assists"})
non_pen_goals_elements = soup.find_all(attrs={"data-stat": "goals_pens"})
penalties_made_elements = soup.find_all(attrs={"data-stat": "pens_made"})

# cards

yellow_cards_elements = soup.find_all(attrs={"data-stat": "cards_yellow"})
red_cards_elements = soup.find_all(attrs={"data-stat": "cards_red"})

# Expected stats
xg_elements = soup.find_all(attrs={"data-stat": "xg"})
npxg_elements = soup.find_all(attrs={"data-stat": "npxg"})
xassists_elements = soup.find_all(attrs={"data-stat": "xg_assist"})

# Progression
progressive_carries_elements = soup.find_all(attrs={"data-stat": "progressive_carries"})
progressive_passes_elements_elements = soup.find_all(attrs={"data-stat": "progressive_passes"})
progressive_passes_recieved_elements = soup.find_all(attrs={"data-stat": "progressive_passes_recieved"})

# Stats per 90
goalsp90_elements = soup.find_all(attrs={"data-stat": "goals_per90"})
assistsp90_elements = soup.find_all(attrs={"data-stat": "assists_per90"})
goalsassistsp90_elements = soup.find_all(attrs={"data-stat": "goals_assists_per90"})
non_pen_goalsp90_elements = soup.find_all(attrs={"data-stat": "goals_pens_per90"})


###

connection = sqlite3.connect('stats.db')
cursor = connection.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS teamStats (
        id INTEGER PRIMARY KEY,
        team_name TEXT,
        xg_value REAL,
        goals_scored INTEGER

    )
''')

# Adding the rest of the columns
cursor.execute("PRAGMA table_info(teamStats)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
# Create a list of columns that need to be added
ColumnsToBeAdded = ['xg_conceded', 'goals_conceded', 'average_age', 'yellow_cards','red_cards','pens_made',
                    'progressive_carries','team_abbreviation','colour_code']
TypeOfData = [' REAL', ' INTEGER', ' REAL', ' INTEGER', 'INTEGER','INTEGER','INTEGER','TEXT','TEXT']

for column, dataType in zip(ColumnsToBeAdded, TypeOfData):
    if column not in column_names:
        # Create a query variable as referencing py variables
        query = "ALTER TABLE teamStats ADD COLUMN " + column  + " " + dataType
        cursor.execute(query)
        connection.commit()

# Add the time

if 'date_and_time' not in column_names:
    cursor.execute('''
    ALTER TABLE teamStats 
    ADD COLUMN date_and_time TEXT 
    ''')
    connection.commit()

cursor.execute('DELETE FROM teamStats')

time_now = datetime.datetime.now()
print(time_now)


# Filtering process to get the stats FOR teams -----------
# Create a variable to ensure there are only 20 teams


def statsPerTeam():
    row = 0
    for team, xg, goals, players, age,yellow,red,pens_made,progressive_carries in zip(team_elements, xg_elements, goals_elements, players_used_elements,
                                             age_elements,yellow_cards_elements,red_cards_elements,penalties_made_elements,progressive_carries_elements):
        team_text = team.get_text(strip=True)
        xg_text = xg.get_text(strip=True)
        goals_text = goals.get_text(strip=True)
        age_text = age.get_text(strip=True)
        yellow_text = yellow.get_text(strip=True)
        red_text = red.get_text(strip=True)
        pens_made_text = pens_made.get_text(strip=True)
        progressive_carries_text =progressive_carries.get_text(strip=True)
        # Filter out players as we only want team stats by checking if there is a value for players_used
        if players:
            # Filter out stats against teams and rows used as headers
            if team_text != "Squad" and "vs" not in team_text:
                # Check if there is an integer value for goals
                if goals_text.isdigit():
                    goals_count = int(goals_text)
                    xg_value = float(xg_text)
                    age_value = float(age_text)
                    yellow_count = int(yellow_text)
                    red_count = int(red_text)
                    pens_made_count = int(pens_made_text)
                    progressive_carries_count = int(progressive_carries_text)
                    print(pens_made_count)
                    # Insert stats into database
                    cursor.execute(
                        'INSERT OR REPLACE into teamStats (team_name, xg_value, goals_scored,average_age,yellow_cards,red_cards,pens_made,progressive_carries,date_and_time) VALUES (?,?,?,?,?,?,?,?,?)',
                        (team_text, xg_value, goals_count, age_value,yellow_count,red_count,pens_made_count,progressive_carries_count,time_now))
                    connection.commit()
                    # print(age_text,possession_text)
                    row += 1
                    # print(row, team_text, xg_value, goals_count)
        if row == 20:
            break


def statsAgainstTeam():
    row = 0
    for team, xg_conceded, goals_conceded, player in zip(team_elements, xg_elements, goals_elements,
                                                         players_used_elements):
        player_count = player.get_text(strip=True)
        if player_count:
            team_text = team.get_text(strip=True)
            if team_text != "Squad" and "vs" in team_text:
                xg_text = xg_conceded.get_text(strip=True)
                goals_text = goals_conceded.get_text(strip=True)
                #Splitting team text, as we need to insert it into original team row
                team_name = team_text.split('vs ')[1]  # Extracts the opponent's name after 'vs '
                xg_value = float(xg_text)
                goals_count = int(goals_text)
                print(team_name)
                cursor.execute('''
                    UPDATE teamStats 
                    SET xg_conceded = ?, goals_conceded = ?
                    WHERE team_name = ?
                ''', (xg_value, goals_count, team_name))

                connection.commit()
                row += 1

        if row == 20:
            break





def TeamConstantInfo():
    team_abbreviations = {
        'Arsenal': 'ARS',
        'Aston Villa': 'AVL',
        'Bournemouth': 'BOU',
        'Brentford': 'BRE',
        'Brighton': 'BHA',
        'Burnley': 'BUR',
        'Chelsea': 'CHE',
        'Crystal Palace': 'CRY',
        'Everton': 'EVE',
        'Fulham': 'FUL',
        'Liverpool': 'LIV',
        'Luton Town': 'LUT',
        'Manchester City': 'MCI',
        'Manchester Utd': 'MUN',
        'Newcastle Utd': 'NEW',
        "Nott'ham Forest": 'NOT',
        'Sheffield Utd': 'SHU',
        'Tottenham': 'TOT',
        'West Ham': 'WHU',
        'Wolves': 'WOL'
    }

    team_colours_hex = {
        'Arsenal': '#EF0107',
        'Aston Villa': '#95BFE5',
        'Bournemouth': '#DA291C',
        'Brentford': '#FFDB00',
        'Brighton': '#0057B8',
        'Burnley': '#6C1D45',
        'Chelsea': '#034694',
        'Crystal Palace': '#1B458F',
        'Everton': '#003399',
        'Fulham': '#000000',
        'Liverpool': '#C8102E',
        'Luton Town': '#FFA500',
        'Manchester City': '#6CADDF',
        'Manchester Utd': '#DA291C',
        'Newcastle Utd': '#241F20',
        "Nott'ham Forest": '#FFCC00',
        'Sheffield Utd': '#EE2737',
        'Tottenham': '#132257',
        'West Ham': '#7A263A',
        'Wolves': '#FDB913'
    }

    for team, abbreviation in team_abbreviations.items():
        hex_code = team_colours_hex.get(team, '')  # Get hex code for the team (if available)
        cursor.execute(
            'UPDATE teamStats SET team_abbreviation = ?, colour_code = ? WHERE team_name = ?',
            (abbreviation, hex_code, team)
        )
        connection.commit()

statsPerTeam()
statsAgainstTeam()
TeamConstantInfo()
cursor.execute('SELECT * FROM teamStats')
data = cursor.fetchall()
for row in data:
    print(row)

# Closing the cursor and connection
cursor.close()
connection.close()
