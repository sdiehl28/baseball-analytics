#!/usr/bin/env python

"""Wrangle Retrosheet Data from {data_dir}/retrosheet/raw to {data_dir}/retrosheet/wrangled

Wrangles: player per game and team per game data
"""

__author__ = 'Stephen Diehl'

import argparse
import re
import shutil
from pathlib import Path
import logging
import sys
import collections

import pandas as pd
import numpy as np

import data_helper as dh

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_parser():
    """Args Description"""

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")
    parser.add_argument("--log", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")

    return parser


def get_game(p_retrosheet_collected):
    """Read in collected results of the cwgame parser."""
    logger.info('Reading game.csv.gz ...')
    filename = p_retrosheet_collected / 'game.csv.gz'
    game = dh.from_csv_with_types(filename)
    n_rows, n_cols = game.shape
    logger.info(f'game loaded {n_rows:,d} rows with {n_cols:,d} columns')
    return game


def get_player_game(p_retrosheet_collected):
    """Read in collected results of the cwdaily parser."""
    logger.info('Reading player_game.csv.gz ...')
    filename = p_retrosheet_collected / 'player_game.csv.gz'
    player_game = dh.from_csv_with_types(filename)
    n_rows, n_cols = player_game.shape
    logger.info(f'player_game loaded {n_rows:,d} rows with {n_cols:,d} columns')
    return player_game


def clean_player_game(player_game):
    """Ensure Primary Key is Unique."""

    # Fix Duplicate Primary Key
    pkey = ['game_id', 'player_id']
    if not dh.is_unique(player_game, pkey):
        # if pkey is dup, sum the stat rows for the dups
        dups = player_game.duplicated(subset=pkey)
        df_dups = player_game.loc[dups, pkey]
        logger.warning(f'Dup PKey Found - summing stats for:\n{df_dups.to_string()}')

        # TODO flag fields should be ORed not summed
        # this is not currently a problem with the single dup found
        # data integrity tests verify that all flag fields are either 0 or 1
        """Flag Fields (value is 0 or 1):
        b_g b_g_dh b_g_ph b_g_pr p_g p_gs p_cg p_sho p_gf p_w p_l p_sv f_p_g f_p_gs f_c_g 
        f_c_gs f_1b_g f_1b_gs f_2b_g f_2b_gs f_3b_g f_3b_gs f_ss_g f_ss_gs f_lf_g f_lf_gs 
        f_cf_g f_cf_gs f_rf_g f_rf_gs     
        """

        # player stat columns b_ for batter, p_ for pitcher, f_ for fielder
        stat_columns = [col for col in player_game.columns if re.search(r'^[bpf]_', col)]
        stat_columns.remove('b_g')  # don't sum this column

        player_game = dh.sum_stats_for_dups(player_game, pkey, stat_columns)

    return player_game


def create_batting(player_game, game_start, p_retrosheet_wrangled):
    """Create batting.csv for batting attributes per player per game."""
    # column names of the batting attributes
    b_cols = [col for col in player_game.columns if col.startswith('b_')]

    # Note: any player who is in a game in any role, will have b_g = 1
    # even if b_pa == 0 (no plate appearances)

    # fields which uniquely identify a record
    pkey = ['game_id', 'player_id']

    # fields to join to other "tables"
    fkey = ['team_id']

    batting = player_game.loc[:, pkey + fkey + b_cols].copy()

    # remove b_ from the column names, except for b_2b and b_3b
    b_cols_new = {col: col[2:] for col in b_cols}
    b_cols_new['b_2b'] = 'double'
    b_cols_new['b_3b'] = 'triple'
    b_cols_new['b_gdp'] = 'gidp'  # to match Lahman
    b_cols_new['b_hp'] = 'hbp'  # to match Lahman
    batting.rename(columns=b_cols_new, inplace=True)

    # add game_start.dt.year as many queries use year
    batting = pd.merge(batting, game_start[['game_id', 'game_start']])
    batting['year'] = batting['game_start'].dt.year.astype('int16')

    dh.optimize_df_dtypes(batting, ignore=['year'])
    logger.info('Writing and compressing batting.  This could take several minutes ...')
    dh.to_csv_with_types(batting, p_retrosheet_wrangled / 'batting.csv.gz')


def create_pitching(player_game, game_start, p_retrosheet_wrangled):
    """Create pitching.csv for pitching attributes per player per game."""
    # column names of the pitching attributes
    p_cols = [col for col in player_game.columns if col.startswith('p_')]

    # if all pitching attributes are 0 then the player did not pitch
    # note: all attributes are unsigned integers, so if their sum is zero, all are zero
    p_filt = player_game[p_cols].sum(axis=1) == 0

    # fields which uniquely identify a record
    pkey = ['game_id', 'player_id']

    # fields to join to other "tables"
    fkey = ['team_id']

    # data with some non-zero attributes
    pitching = player_game.loc[~p_filt, pkey + fkey + p_cols].copy()

    # remove p_ from the column names, except for p_2b and p_3b
    p_cols_new = {col: col[2:] for col in p_cols}
    p_cols_new['p_2b'] = 'double'
    p_cols_new['p_3b'] = 'triple'
    p_cols_new['p_gdp'] = 'gidp'  # to match Lahman
    p_cols_new['p_hp'] = 'hbp'  # to match Lahman
    pitching.rename(columns=p_cols_new, inplace=True)

    # add game_start.dt.year as many queries use year
    pitching = pd.merge(pitching, game_start[['game_id', 'game_start']])
    pitching['year'] = pitching['game_start'].dt.year.astype('int16')

    dh.optimize_df_dtypes(pitching, ignore=['year'])
    logger.info('Writing and compressing pitching.  This could take several minutes ...')
    dh.to_csv_with_types(pitching, p_retrosheet_wrangled / 'pitching.csv.gz')


def create_fielding(player_game, game_start, p_retrosheet_wrangled):
    """Create fielding.csv for fielding attributes per player per game."""
    # column names for fielding attributes
    f_cols = [col for col in player_game.columns if col.startswith('f_')]

    # create orig_cols dictionary which maps fielder's pos to original fielding columns names
    # create new_cols dictionary which maps fielder's pos to new fielding column names
    # pos: P, C, 1B, 2B, 3B, SS, LF, CF, RF
    # column name pattern: f_{pos}_{stat}
    orig_cols = collections.defaultdict(list)
    new_cols = collections.defaultdict(list)
    for col in f_cols:
        match = re.search(r'f_(\w{1,2})_(\w*)', col)
        pos = match.group(1)
        stat = match.group(2)
        orig_cols[pos].append(col)
        stat = stat.replace('out', 'inn_outs')  # to match Lahman
        new_cols[pos].append(stat)

    # full pkey will be: ['game_id', 'player_id', 'pos']
    pkey = ['game_id', 'player_id']

    # fields to join to other "tables"
    fkey = ['team_id']

    """For each record created by cwdaily, create up to 9 new records, one per position.
    Each record will temporarily go in its own dataframe and then be concatenated.
    
    Each dataframe has the same columns."""
    dfs = []
    for pos in orig_cols.keys():
        # if all fielding attributes for this pos are 0 then the player did not play that pos
        # note: all attributes are unsigned integers
        f_filt = player_game[orig_cols[pos]].sum(axis=1) == 0

        df = pd.DataFrame()
        df[pkey + fkey + new_cols[pos]] = \
            player_game.loc[~f_filt, pkey + fkey + orig_cols[pos]].copy()

        # add the position column to the df
        # use upper case to match Lahman position values
        df.insert(2, 'pos', pos.upper())

        # orig_cols['c'] has pb and xi columns
        # all other positions do not have pb and xi
        if pos != 'c':
            df[f'pb'] = 0
            df[f'xi'] = 0

        dfs.append(df)

    fielding = pd.concat(dfs, ignore_index=True)

    # add game_start.dt.year as many queries use year
    fielding = pd.merge(fielding, game_start[['game_id', 'game_start']])
    fielding['year'] = fielding['game_start'].dt.year.astype('int16')

    dh.optimize_df_dtypes(fielding, ignore=['year'])
    logger.info('Writing and compressing fielding.  This could take several minutes ...')
    dh.to_csv_with_types(fielding, p_retrosheet_wrangled / 'fielding.csv.gz')


def wrangle_game(game, p_retrosheet_wrangled):
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

    # include opponent team_id in each row
    home_team_game.insert(4, 'opponent_team_id', away_team_game['team_id'])
    away_team_game.insert(4, 'opponent_team_id', home_team_game['team_id'])
    team_game = pd.concat([home_team_game, away_team_game])

    # improve column names
    names = {col: col.replace('_ct', '') for col in team_game.columns if col.endswith('_ct')}

    # handle invalid identifiers
    names['2b_ct'] = 'double'
    names['3b_ct'] = 'triple'

    # pitcher_ct (number of pitchers) is a good name though, keep it
    names.pop('pitcher_ct')

    # additional fields to rename for consistency
    names['bi_ct'] = 'rbi'
    names['gdp_ct'] = 'gidp'
    names['hits_ct'] = 'h'
    names['hp_ct'] = 'hbp'
    names['err_ct'] = 'e'
    names['score_ct'] = 'r'

    team_game = team_game.rename(columns=names)

    # create new datetime column
    game_tidy['game_start'] = game_tidy.apply(parse_datetime, axis=1)
    game_tidy = dh.move_column_after(game_tidy, 'game_id', 'game_start')

    # these fields are no longer necessary
    game_tidy = game_tidy.drop(['start_game_tm', 'game_dt', 'game_dy'], axis=1)

    # add the game_start column to team_game to simplify queries
    team_game = pd.merge(team_game, game_tidy[['game_id', 'game_start']])
    team_game['year'] = team_game['game_start'].dt.year.astype('int16')

    logger.info('Writing and compressing team_game.  This could take several minutes ...')
    dh.optimize_df_dtypes(team_game, ignore=['year'])
    dh.to_csv_with_types(team_game, p_retrosheet_wrangled / 'team_game.csv.gz')

    # convert designated hitter to True/False and rename
    game_tidy['dh'] = False
    filt = game_tidy['dh_fl'] == 'T'
    game_tidy.loc[filt, 'dh'] = True
    game_tidy.drop('dh_fl', axis=1, inplace=True)

    # convert impossible attendance values to null and rename
    filt = game_tidy['attend_park_ct'] <= 0
    impossible_values = game_tidy.loc[filt, 'attend_park_ct'].unique()
    game_tidy['attendance'] = game_tidy['attend_park_ct'].replace(impossible_values, np.nan)
    game_tidy.drop('attend_park_ct', axis=1, inplace=True)

    # convert impossible temperature values to null and rename
    filt = game_tidy['temp_park_ct'] <= 0
    impossible_values = game_tidy.loc[filt, 'temp_park_ct'].unique()
    game_tidy['temperature'] = game_tidy['temp_park_ct'].replace(impossible_values, np.nan)
    game_tidy.drop('temp_park_ct', axis=1, inplace=True)

    # replace code values with strings
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-winddirection
    direction = {
        0: 'unknown',
        1: 'to_lf',
        2: 'to_cf',
        3: 'to_rf',
        4: 'l_to_r',
        5: 'from_lf',
        6: 'from_cf',
        7: 'from_rf',
        8: 'r_to_l'}
    game_tidy['wind_direction'] = \
        game_tidy['wind_direction_park_cd'].map(direction).replace('unknown', np.nan)
    game_tidy.drop('wind_direction_park_cd', axis=1, inplace=True)

    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-windspeed
    # convert impossible wind speed values to null and rename
    filt = game_tidy['wind_speed_park_ct'] < 0
    impossible_values = game_tidy.loc[filt, 'wind_speed_park_ct'].unique()
    game_tidy['wind_speed'] = game_tidy['wind_speed_park_ct'].replace(impossible_values, np.nan)
    game_tidy.drop('wind_speed_park_ct', axis=1, inplace=True)

    # replace code values with strings
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-fieldcondition
    condition = {
        0: 'unknown',
        1: 'soaked',
        2: 'wet',
        3: 'damp',
        4: 'dry'}
    game_tidy['field_condition'] = \
        game_tidy['field_park_cd'].map(condition).replace('unknown', np.nan)
    game_tidy.drop('field_park_cd', axis=1, inplace=True)

    # replace code values with strings
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-precipitation
    precip = {
        0: 'unknown',
        1: 'none',
        2: 'drizzle',
        3: 'showers',
        4: 'rain',
        5: 'snow'}
    game_tidy['precip_type'] = \
        game_tidy['precip_park_cd'].map(precip).replace('unknown', np.nan)
    game_tidy.drop('precip_park_cd', axis=1, inplace=True)

    # replace code values with strings
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-sky
    sky = {
        0: 'unknown',
        1: 'sunny',
        2: 'cloudy',
        3: 'overcast',
        4: 'night',
        5: 'dome'}
    game_tidy['sky_condition'] = \
        game_tidy['sky_park_cd'].map(sky).replace('unknown', np.nan)
    game_tidy.drop('sky_park_cd', axis=1, inplace=True)

    # rename a few fields
    new_names = {'minutes_game_ct': 'game_length_minutes',
                 'inn_ct': 'game_length_innings',
                 'outs_ct': 'game_length_outs'}
    game_tidy.rename(columns=new_names, inplace=True)

    logger.info('Writing and compressing game.  This could take several minutes ...')
    dh.optimize_df_dtypes(game_tidy)
    dh.to_csv_with_types(game_tidy, p_retrosheet_wrangled / 'game.csv.gz')

    # to add game date to other tables
    return game_tidy[['game_id', 'game_start']]


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

    if 0 < time < 900:
        time += 1200
    elif (900 <= time < 1200) and day_night == 'N':
        time += 1200

    time_str = f'{time // 100:02d}:{time % 100:02d}'
    datetime_str = str(date) + ' ' + time_str
    return pd.to_datetime(datetime_str, format='%Y%m%d %H:%M')


def wrangle_event(p_retrosheet_collected, p_retrosheet_wrangled):
    """Wrangle event

    At this time, there is nothing to do, just copy the collected data."""
    source = p_retrosheet_collected / 'event.csv.gz'
    destination = p_retrosheet_wrangled / 'event.csv.gz'
    shutil.copyfile(source, destination)

    source = p_retrosheet_collected / 'event_types.csv'
    destination = p_retrosheet_wrangled / 'event_types.csv'
    shutil.copyfile(source, destination)


def wrangle_parks(data_dir, retrosheet_wrangle):
    parks_filename = data_dir / 'retrosheet/raw/misc/parkcode.txt'
    parks = pd.read_csv(parks_filename, parse_dates=['START', 'END'])
    cols = [col.lower() for col in parks.columns]
    parks.columns = cols
    parks = parks.rename(columns={'parkid': 'park_id'})
    dh.to_csv_with_types(parks, retrosheet_wrangle / 'parks.csv')


def wrangle_teams(data_dir, retrosheet_wrangle):
    team_dir = data_dir / 'retrosheet/raw/event/regular'

    dfs = []
    team_files = team_dir.glob('TEAM*')
    for team in sorted(team_files):
        year = int(team.name[-4:])
        df = pd.read_csv(team, header=None, names=['team_id', 'lg_id', 'city', 'name'])
        df.insert(1, 'year', year)
        dfs.append(df)
    retro_teams = pd.concat(dfs, ignore_index=True)
    dh.to_csv_with_types(retro_teams, retrosheet_wrangle / 'teams.csv')


def main():
    """Wrangle the data.
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

    data_dir = Path(args.data_dir)
    p_retrosheet_collected = (data_dir / 'retrosheet/collected').resolve()
    p_retrosheet_wrangled = (data_dir / 'retrosheet/wrangled').resolve()

    # get collected data from parsers
    game = get_game(p_retrosheet_collected)  # cwgame
    game_start = wrangle_game(game, p_retrosheet_wrangled)

    player_game = get_player_game(p_retrosheet_collected)  # cwdaily
    player_game = clean_player_game(player_game)

    create_batting(player_game, game_start, p_retrosheet_wrangled)
    create_pitching(player_game, game_start, p_retrosheet_wrangled)
    create_fielding(player_game, game_start, p_retrosheet_wrangled)

    wrangle_event(p_retrosheet_collected, p_retrosheet_wrangled)  # cwevent

    # parks.txt is included with the retrosheet data.  It is a csv file.
    wrangle_parks(data_dir, p_retrosheet_wrangled)

    # TEAM<YYYY> is included in the retrosheet data.  They are csv files.
    wrangle_teams(data_dir, p_retrosheet_wrangled)

    logger.info('Finished')


if __name__ == '__main__':
    main()
