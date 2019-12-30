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
import collections

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

        # TODO flag fields should be ORed not summed
        # as there is only 1 dup record and summing the flags does not produce a 2
        # in any flag column, this is not currently a problem
        """Flag Fields:
        b_g b_g_dh b_g_ph b_g_pr p_g p_gs p_cg p_sho p_gf p_w p_l p_sv f_p_g f_p_gs f_c_g 
        f_c_gs f_1b_g f_1b_gs f_2b_g f_2b_gs f_3b_g f_3b_gs f_ss_g f_ss_gs f_lf_g f_lf_gs 
        f_cf_g f_cf_gs f_rf_g f_rf_gs     
        """

        player_game = dh.sum_stats_for_dups(player_game, pkey, stat_columns)

    # Remove appear_dt as it has same values as game_dt
    if (player_game['game_dt'] == player_game['appear_dt']).mean() > 0.999:
        player_game.drop('appear_dt', axis=1, inplace=True)

    # batting and pitching
    b_cols = [col for col in stat_columns if col.startswith('b_')]
    p_cols = [col for col in stat_columns if col.startswith('p_')]

    # if all attributes for a given role are 0, then the player did not take on that role
    # however all players have b_g = 1, even if b_pa == 0 (no plate appearances)
    # b_filt = player_game[b_cols].sum(axis=1) == 0  # no rows meet this criteria
    p_filt = player_game[p_cols].sum(axis=1) == 0

    # fields which uniquely identify a record
    pkey = ['game_id', 'player_id']

    # data with some non-zero attributes
    batting = player_game.loc[:, pkey + b_cols].copy()
    pitching = player_game.loc[~p_filt, pkey + p_cols].copy()

    # remove b_ and p_
    b_cols_new = {col: col[2:] for col in b_cols if col[2] != '2' and col[2] != '3'}
    p_cols_new = {col: col[2:] for col in p_cols if col[2] != '2' and col[2] != '3'}

    batting.rename(columns=b_cols_new, inplace=True)
    pitching.rename(columns=p_cols_new, inplace=True)

    logger.info('Writing and compressing batting.  This could take several minutes ...')
    dh.to_csv_with_types(batting, p_retrosheet_wrangled / 'batting.csv.gz')

    logger.info('Writing and compressing pitching.  This could take several minutes ...')
    dh.to_csv_with_types(pitching, p_retrosheet_wrangled / 'pitching.csv.gz')

    # fielding
    f_cols = [col for col in stat_columns if col.startswith('f_')]

    # decompose the fielding field names
    # f_{pos}_{stat}
    orig_cols = collections.defaultdict(list)
    new_cols = collections.defaultdict(list)
    for col in f_cols:
        match = re.search(r'f_(\w{1,2})_(\w*)', col)
        pos = match.group(1)
        stat = match.group(2)
        orig_cols[pos].append(col)
        stat = stat.replace('out', 'inn_outs')  # to match Lahman
        new_cols[pos].append(stat)

    # create 9 dfs, one per position
    # all having the same columns
    dfs = []
    for key in orig_cols.keys():
        # are all attributes for this position zero
        f_filt = player_game[orig_cols[key]].sum(axis=1) == 0

        # create a new df using new columns from the original for rows with data
        df = pd.DataFrame()
        df[pkey + new_cols[key]] = player_game.loc[~f_filt, pkey + orig_cols[key]].copy()

        # add the position column
        df.insert(2, 'pos', key.upper())

        # these are always zero for non-catchers
        if key != 'c':
            df[f'pb'] = 0
            df[f'xi'] = 0

        dfs.append(df)

    fielding_new = pd.concat(dfs, ignore_index=True)
    dh.optimize_df_dtypes(fielding_new)
    logger.info('Writing and compressing fielding.  This could take several minutes ...')
    dh.to_csv_with_types(fielding_new, p_retrosheet_wrangled / 'fielding.csv.gz')

    # create and persist dictionaries to map retrosheet player_id to lahman player_id
    # and retrosheet team_id to lahman team_id
    lahman_people_fn = p_retrosheet_collected.parent.parent / 'lahman/wrangled/people.csv'
    lahman_people = dh.from_csv_with_types(lahman_people_fn)

    lahman_teams_fn = p_retrosheet_collected.parent.parent / 'lahman/wrangled/teams.csv'
    lahman_teams = dh.from_csv_with_types(lahman_teams_fn)

    # from (at least) 1955 on, there are no players in Retrosheet that are missing in Lahman's People.csv
    # Lahman uses the filed 'retro_id' to represent the Retrosheet player_id
    r_players = player_game['player_id'].unique()
    l_players = lahman_people['retro_id'].unique()

    # only need player_ids that are in Retrosheet
    filt = lahman_people['retro_id'].isin(r_players)

    pp = lahman_people.loc[filt, ['player_id', 'retro_id']].copy()
    pp.set_index('retro_id', inplace=True)
    pp_dict = pp.to_dict()['player_id']

    # TODO move this to test_data.py after reading it in
    # verify dictionary keys contains all retrosheet players
    assert set(r_players).issubset(set(pp_dict.keys()))

    # same for teams
    r_teams = player_game['team_id'].unique()
    l_teams = lahman_teams['team_id_retro'].unique()

    # only need teams that are in Retrosheet
    filt = lahman_teams['team_id_retro'].isin(r_teams)

    tt = lahman_teams.loc[filt, ['year_id', 'team_id', 'team_id_retro']].copy()
    tt.set_index(['year_id', 'team_id_retro'], inplace=True)
    tt_dict = tt.to_dict()['team_id']

    # TODO move this to test_data.py after reading it in
    # spot check
    assert tt_dict[(2013, 'ANA')] == 'LAA'

    # TODO write tt and pp to disk


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

    logger.info('Writing and compressing team_game.  This could take several minutes ...')
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

    logger.info('Writing and compressing game.  This could take several minutes ...')
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

    logger.info('Finished.')


if __name__ == '__main__':
    main()
