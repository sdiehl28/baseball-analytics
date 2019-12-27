#!/usr/bin/env python

"""Wrangle Retrosheet Data from {data_dir}/retrosheet/raw to {data_dir}/retrosheet/wrangled

Wrangles: player per game and team per game data
"""

__author__ = 'Stephen Diehl'

import argparse
import re
from pathlib import Path
import logging
import sys

import pandas as pd

import data_helper as dh

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_parser():
    """Args Description"""

    # current_year = datetime.datetime.today().year
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")
    parser.add_argument("--log", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")

    return parser


def wrangle_player_per_game(p_retrosheet_collected, p_retrosheet_wrangled):
    logger.info('Reading player_game.csv.gz ...')
    filename = p_retrosheet_collected / 'player_game.csv.gz'
    player_game = dh.from_csv_with_types(filename)
    logger.info('player_game loaded')

    # Fix Duplicate Primary Key
    pkey = ['game_id', 'player_id']
    if not dh.is_unique(player_game, pkey):
        # if pkey is dup, sum the stat rows for the dups
        dups = player_game.duplicated(subset=pkey)
        df_dups = player_game.loc[dups, pkey]
        logger.warning(f'Dup PKey Found\n{df_dups.to_string()}')

        # player stat columns b_ for batter, p_ for pitcher, f_ for fielder
        stat_columns = [col for col in player_game.columns if re.search(r'^[bpf]_', col)]

        # sum all stat columns except the game column
        stat_columns.remove('b_g')

        player_game = dh.sum_stats_for_dups(player_game, pkey, stat_columns)

    # Remove appear_dt as it has same values as game_dt
    if (player_game['game_dt'] == player_game['appear_dt']).mean() > 0.999:
        player_game.drop('appear_dt', axis=1, inplace=True)

    # Add Lahman player_id to make joins with Lahman easier later
    lahman_people_fn = p_retrosheet_collected.parent.parent / 'lahman/wrangled/people.csv'
    lahman_people = dh.from_csv_with_types(lahman_people_fn)

    lahman_teams_fn = p_retrosheet_collected.parent.parent / 'lahman/wrangled/teams.csv'
    lahman_teams = dh.from_csv_with_types(lahman_teams_fn)

    # add player_id from Lahman to make joins on players easier
    # retrosheet.player_game JOIN lahman.people ON player_id = retro_id
    player_game = pd.merge(player_game, lahman_people[['player_id', 'retro_id']],
                           left_on='player_id', right_on='retro_id',
                           suffixes=['', '_lahman'])

    # the retro_id from Lahman is not needed
    player_game.drop('retro_id', axis=1, inplace=True)

    # move the new player_id_lahman column to be after player_id
    player_game = dh.move_column_after(player_game, 'player_id', 'player_id_lahman')

    # add year_id to player_game (for use with Lahman teams)
    player_game['year_id'] = player_game['game_dt'] // 10000
    player_game = dh.move_column_after(player_game, 'game_dt', 'year_id')

    # add team_id from Lahman to make joins on teams easier
    # r.player_game JOIN l.teams ON r.year_id = l.year_id AND r.team_id = l.team_id_retro
    player_game = pd.merge(player_game, lahman_teams[['team_id', 'year_id', 'team_id_retro']],
                           left_on=['year_id', 'team_id'],
                           right_on=['year_id', 'team_id_retro'],
                           suffixes=['', '_lahman'])

    # the team retro_id from Lahman is not needed
    player_game.drop('team_id_retro', axis=1, inplace=True)

    # move the new team_id_lahman column to be after team_id
    player_game = dh.move_column_after(player_game, 'team_id', 'team_id_lahman')

    logger.info('Writing and compressing player_game.  This could take several minutes ...')
    dh.to_csv_with_types(player_game, p_retrosheet_wrangled / 'player_game.csv.gz')
    logger.info('player_game written.')


def wrangle_game(p_retrosheet_collected, p_retrosheet_wrangled):
    """Tidy the Game Data

    There are 3 types of data:

    data specific to a game -- the 'game' columns below
    data specific to the home team for that game -- the 'home' columns below
    data specific to the away team for that game -- the 'away' columns below
    The attributes for the home team are identical to the attributes for the away team.

    This suggests breaking this out into 2 csv files.

    1. team_game.csv with key (game_id, team_id) -- stats per team per game (e.g. runs scored)
    2. game.csv with key (game_id) -- stats per game (e.g. attendance)
    """
    filename = p_retrosheet_collected / 'game.csv.gz'
    game = dh.from_csv_with_types(filename)

    home_cols = [col for col in game.columns if col.startswith('home')]
    away_cols = [col for col in game.columns if col.startswith('away')]
    game_cols = [col for col in game.columns
                 if not col.startswith('home') and not col.startswith('away')]

    game_tidy = game[game_cols].copy()
    home_team_game = game[['game_id'] + home_cols].copy()
    away_team_game = game[['game_id'] + away_cols].copy()

    home_team_game['at_home'] = True
    away_team_game['at_home'] = False
    home_team_game = dh.move_column_after(home_team_game, 'game_id', 'at_home')
    away_team_game = dh.move_column_after(away_team_game, 'game_id', 'at_home')

    # remove leading 'home_' and 'away_' suffix from fields
    home_team_game.rename(columns=lambda col: col[5:] if col.startswith('home_') else col, inplace=True)
    away_team_game.rename(columns=lambda col: col[5:] if col.startswith('away_') else col, inplace=True)

    team_game = pd.concat([home_team_game, away_team_game])

    # improve column names
    names = {col: col.replace('_ct', '') for col in team_game.columns if col.endswith('_ct')}

    # handle invalid identifiers
    names['2b_ct'] = 'b_2b'
    names['3b_ct'] = 'b_3b'

    # pitcher_ct (number of pitchers) is a good name though, keep it
    names.pop('pitcher_ct')

    team_game = team_game.rename(columns=names)
    dh.optimize_df_dtypes(team_game)
    dh.to_csv_with_types(team_game, p_retrosheet_wrangled / 'team_game.csv.gz')

    # create new datetime column
    game_tidy['game_start_dt'] = game_tidy.apply(parse_datetime, axis=1)
    game_tidy = dh.move_column_after(game_tidy, 'game_id', 'game_start_dt')

    # these are no longer necessary
    game_tidy = game_tidy.drop(['start_game_tm', 'game_dt', 'game_dy'], axis=1)

    # convert designated hitter flag to True/False
    game_tidy['dh_flag'] = False
    filt = game_tidy['dh_fl'] == 'T'
    game_tidy.loc[filt, 'dh_flag'] = True
    game_tidy.drop('dh_fl', axis=1, inplace=True)

    dh.optimize_df_dtypes(game_tidy)
    dh.to_csv_with_types(game_tidy, p_retrosheet_wrangled / 'game.csv.gz')


def parse_datetime(row):
    """Determine AM/PM from MLB domain knowledge and Day/Night Flag

    Here is the relevant information.

    * am/pm is not specified
    * start_game_tm is an integer
      * example: 130 represents 1:30 (am or pm)
    * start_game_tm == 0 means the game start time is unknown
    * there are no start_game_tm < 100 that are not exactly zero
    * daynight_park_cd is never missing
    * based on the data, almost always a game that starts between 5 and 9 is classified as a night game
      This is likely because "night" actually means that the stadium lights must be turned on before a
      game of typical length ends.
    * MLB domain knowledge: A game may start "early" to allow for travel, but games never start
      before 9 am so: 100 <= start_game_tm < 900 => pm
      * example: 830 => 8:30 pm
    * MLB domain knowledge: A game may start "late" due to rain delay, but games never start
      after midnight so: 900 < start_game_tm < 1200 => am or pm depending on the day/night flag
      * example: 1030 Day => 10:30 am
      * example: 1030 Night => 10:30 pm
    """
    date = row['game_dt']
    time = row['start_game_tm']
    day_night = row['daynight_park_cd']

    if time > 0 and time < 900:
        time += 1200
    elif (900 <= time < 1200) and day_night == 'N':
        time += 1200

    time_str = f'{time // 100:02d}:{time % 100:02d}'
    datetime_str = str(date) + ' ' + time_str
    return pd.to_datetime(datetime_str, format='%Y%m%d %H:%M')


def main():
    """Perform the data transformations
    """
    parser = get_parser()
    args = parser.parse_args()

    if args.log_level:
        fh = logging.FileHandler('download.log')
        formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s')
        fh.setFormatter(formatter)
        fh.setLevel(args.log_level)
        logger.addHandler(fh)

    if args.verbose:
        # send INFO level logging to stdout
        sh = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s')
        sh.setFormatter(formatter)
        sh.setLevel(logging.INFO)
        logger.addHandler(sh)

    p_retrosheet_collected = Path(args.data_dir).joinpath('retrosheet/collected').resolve()
    p_retrosheet_wrangled = Path(args.data_dir).joinpath('retrosheet/wrangled').resolve()

    wrangle_player_per_game(p_retrosheet_collected, p_retrosheet_wrangled)
    wrangle_game(p_retrosheet_collected, p_retrosheet_wrangled)


if __name__ == '__main__':
    main()
