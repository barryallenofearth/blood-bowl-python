import os.path

import pandas as pd

from database import database
from database.database import db, Season, Coach, Race, Team, League, BBMatch, AdditionalStatistics
from util import formatting


def init_database():
    def init_leagues():
        leagues_csv = "data/leagues.csv"
        if not os.path.exists(leagues_csv):
            return
        init_file = pd.read_csv(leagues_csv, delimiter=";")
        for league_index, league_data in init_file.iterrows():
            league = League()
            league.name = league_data["name"]
            league.short_name = league_data["short_name"]
            league.is_selected = league_data["is_selected"]
            db.session.add(league)

        db.session.commit()

    def league_id_by_short_name(short_name):
        league = db.session.query(League).filter_by(short_name=short_name).first()
        if league is None:
            raise ValueError(f"League '{short_name}' not found.")
        return league.id

    def season_id_by_short_name(season_short_name: str, league_short_name: str):
        season = db.session.query(Season).filter_by(short_name=season_short_name).filter_by(league_id=league_id_by_short_name(league_short_name)).first()
        if season is None:
            raise ValueError(f"League '{season_short_name}' not found.")
        return season.id

    def init_seasons():
        seasons_csv = "data/seasons.csv"
        if not os.path.exists(seasons_csv):
            return
        init_file = pd.read_csv(seasons_csv, delimiter=";")
        for season_index, season_data in init_file.iterrows():
            season = Season()
            season.league_id = league_id_by_short_name(season_data["league_short_name"])
            season.name = season_data["name"]
            season.short_name = season_data["short_name"]
            season.is_selected = season_data["is_selected"]
            db.session.add(season)
            db.session.commit()

            database.persist_scorings(season_data["scorings"].replace("\\n", "\n"), season.id)

    def init_races():

        races_csv = "data/races.csv"
        if not os.path.exists(races_csv):
            return
        init_file = pd.read_csv(races_csv, delimiter=";")
        for race_index, race_data in init_file.iterrows():
            race = Race()
            race.name = race_data["name"]

            db.session.add(race)

        db.session.commit()

    def __team_id_by_name(team_name: str, season_id: int):
        team = db.session.query(Team).filter_by(name=team_name).filter_by(season_id=season_id).first()
        if team is None:
            raise ValueError(f"Team '{team_name}' not found.")
        return team.id

    def init_teams_and_coaches():
        def race_id_by_name(name: str) -> int:
            race = db.session.query(Race).filter_by(name=name).first()

            if race is None:
                raise ValueError(f"Race '{name}' not found.")
            return race.id

        def coach_id_by_name(first_name: str, last_name: str, display_name: str) -> int:
            coach = db.session.query(Coach) \
                .filter_by(first_name=first_name.strip()) \
                .filter_by(last_name=last_name.strip()) \
                .filter_by(display_name=display_name.strip()) \
                .first()
            if coach is None:
                coach = Coach()
                coach.first_name = first_name.strip()
                coach.last_name = last_name.strip()
                coach.display_name = display_name.strip()

                db.session.add(coach)
                db.session.commit()

                return coach.id

            return coach.id

        coaches_csv = "data/teams_and_coaches.csv"
        if not os.path.exists(coaches_csv):
            return
        init_file = pd.read_csv(coaches_csv, delimiter=";")
        for team_index, team_data in init_file.iterrows():
            team = Team()
            team.season_id = season_id_by_short_name(team_data["season_short_name"], team_data["league_short_name"])
            team.name = team_data["name"]
            team.short_name = formatting.generate_team_short_name(team.name)
            team.race_id = race_id_by_name(team_data["race_name"])
            team.coach_id = coach_id_by_name(team_data["coach_first_name"], team_data["coach_last_name"], team_data["coach_display_name"])
            team.is_disqualified = team_data["is_disqualified"]
            db.session.add(team)

        db.session.commit()

    def init_matches():

        matches_csv = "data/matches.csv"
        if not os.path.exists(matches_csv):
            return
        init_file = pd.read_csv(matches_csv, delimiter=";")
        for team_index, match_data in init_file.iterrows():
            match = BBMatch()
            match.match_number = match_data["match_number"]
            match.season_id = season_id_by_short_name(match_data["season_short_name"], match_data["league_short_name"])
            match.team_1_id = __team_id_by_name(match_data["team1"], match.season_id)
            match.team_2_id = __team_id_by_name(match_data["team2"], match.season_id)
            match.team_1_touchdown = match_data["td_team_1"]
            match.team_2_touchdown = match_data["td_team_2"]
            match.team_1_point_modification = match_data["point_modification_team_1"]
            match.team_2_point_modification = match_data["point_modification_team_2"]
            match.team_1_surrendered = match_data["team_1_surrendered"]
            match.team_2_surrendered = match_data["team_2_surrendered"]
            match.is_team_1_victory_by_kickoff = match_data["is_team_1_victory_by_kickoff"]
            match.is_team_2_victory_by_kickoff = match_data["is_team_2_victory_by_kickoff"]
            match.is_playoff_match = match_data["is_playoff_match"]
            match.is_tournament_match = match_data["is_tournament_match"]
            db.session.add(match)
        db.session.commit()

    def init_additional_statistics():
        statistics_csv = "data/additional_statistics.csv"
        if not os.path.exists(statistics_csv):
            return
        init_file = pd.read_csv(statistics_csv, delimiter=";")

        for additional_statistics_index, additional_statistics_data in init_file.iterrows():
            season_short_name = additional_statistics_data["season_short_name"]
            league_short_name = additional_statistics_data["league_short_name"]
            season_id = season_id_by_short_name(season_short_name, league_short_name)

            additional_statistics = AdditionalStatistics()
            additional_statistics.season_id = season_id
            additional_statistics.team_id = __team_id_by_name(additional_statistics_data["team_name"], season_id)
            additional_statistics.casualties = additional_statistics_data["casualties"]
            db.session.add(additional_statistics)
            db.session.commit()

    if db.session.query(League).count() == 0:
        init_leagues()
        init_seasons()
        init_races()
        init_teams_and_coaches()
        init_matches()
        init_additional_statistics()
