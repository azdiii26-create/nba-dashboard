import pandas as pd
import requests
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import leaguedashteamstats
from nba_api.live.nba.endpoints import scoreboard

def get_active_players():
    player_list = players.get_players()
    active_players = [
        {
            'Player Name': player.get('full_name', ''),
            'Player ID': player.get('id', ''),
            'Team ID': player.get('team_id', ''),
            'Position': player.get('position', ''),
        }
        for player in player_list
    ]
    return active_players

def get_player_game_log(player_id, season):
    try:
        game_log = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=season
        ).get_data_frames()[0]
        game_log['PTS+REB'] = game_log['PTS'] + game_log['REB']
        game_log['PTS+AST'] = game_log['PTS'] + game_log['AST']
        game_log['AST+REB'] = game_log['AST'] + game_log['REB']
        game_log['PTS+AST+REB'] = game_log['PTS'] + game_log['AST'] + game_log['REB']
        game_log = game_log.sort_values(by='GAME_DATE', ascending=True)
        return game_log
    except Exception as e:
        print(f"Error fetching player game log: {e}")
        return pd.DataFrame()

def get_nba_teams():
    nba_teams = teams.get_teams()
    return sorted(nba_teams, key=lambda x: x['full_name'])

def get_team_roster(team_id):
    try:
        roster = commonteamroster.CommonTeamRoster(team_id=team_id)
        df = roster.get_data_frames()[0]
        return [
            {
                'Player Name': row['PLAYER'],
                'Player ID': row['PLAYER_ID'],
                'Position': row['POSITION']
            }
            for _, row in df.iterrows()
        ]
    except Exception:
        return []

def get_opponent_defense_stats(season='2026-27'):
    try:
        stats = leaguedashteamstats.LeagueDashTeamStats(
            season=season,
            measure_type_detailed_defense='Opponent',
            per_mode_detailed='PerGame'
        )
        df = stats.get_data_frames()[0]

        # Łączone statystyki pozwalane przeciwnikom
        df['OPP_PTS+REB'] = df['OPP_PTS'] + df['OPP_REB']
        df['OPP_PTS+AST'] = df['OPP_PTS'] + df['OPP_AST']
        df['OPP_AST+REB'] = df['OPP_AST'] + df['OPP_REB']
        df['OPP_PTS+AST+REB'] = df['OPP_PTS'] + df['OPP_AST'] + df['OPP_REB']

        return df
    except Exception:
        return pd.DataFrame()

def get_todays_games():
    try:
        board = scoreboard.ScoreBoard()
        games = board.games.get_dict()
        todays_list = []
        for g in games:
            away_name = g['awayTeam']['teamCity'] + " " + g['awayTeam']['teamName']
            home_name = g['homeTeam']['teamCity'] + " " + g['homeTeam']['teamName']
            status = g['gameStatusText']
            todays_list.append({
                'away_id': g['awayTeam']['teamId'],
                'home_id': g['homeTeam']['teamId'],
                'label': f"{away_name} @ {home_name} ({status})"
            })
        return todays_list
    except Exception:
        return []

def get_injured_players():
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
    injured = {}
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for team in data.get("injuries", []):
            for item in team.get("injuries", []):
                name = item.get("athlete", {}).get("displayName", "")
                status = item.get("status", "Kontuzja")
                if name:
                    injured[name.lower()] = status
        return injured
    except Exception:
        return {}

def get_team_pace_stats(season='2026-27'):
    try:
        stats = leaguedashteamstats.LeagueDashTeamStats(
            season=season,
            measure_type_detailed_defense='Advanced',
            per_mode_detailed='PerGame'
        )
        df = stats.get_data_frames()[0]
        return df[['TEAM_ID', 'TEAM_NAME', 'PACE', 'PACE_RANK', 'NET_RATING', 'NET_RATING_RANK']]
    except Exception:
        return pd.DataFrame()

# Przykład użycia:
# active_players = get_active_players()
# print(active_players)

# player_id = 201939  # Przykład ID Lebron James
# season = '2021-22'  # Przykład bieżącego sezonu
# game_log = get_player_game_log(player_id, season)
# print(game_log)