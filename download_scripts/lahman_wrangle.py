#!/usr/bin/env python

"""Wrangle Lahman Data from {data_dir}/lahman/raw to {data_dir}/lahman/wrangled

Wrangles: people, batting, pitching, fielding, and teams
"""

__author__ = 'Stephen Diehl'

import pandas as pd

import os
import argparse
from pathlib import Path
import logging
import sys
import data_helper as dh


def get_fieldname_mapping():
    """Dictionary of fieldnames that will be modified."""

    # It is easier to maintain fieldname mappings in a single location
    new_names = {
        'playerID': 'player_id',
        'yearID': 'year_id',
        'teamID': 'team_id',
        'lgID': 'lg_id',
        'GIDP': 'gdp',  # to be consistent with retrosheet
        '2B': 'b_2b',
        '3B': 'b_3b',
        'BAOpp': 'ba_opp',
        'IPouts': 'ip_outs',
        'InnOuts': 'inn_outs',
        'franchID': 'franch_id',
        'divID': 'div_id',
        'Ghome': 'g_home',
        'DivWin': 'div_win',
        'WCWin': 'wc_win',
        'LgWin': 'lg_win',
        'WSWin': 'ws_win',
        'teamIDBR': 'team_id_br',
        'teamIDlahman45': 'team_id_lahman45',
        'teamIDretro': 'team_id_retro',
        'birthYear': 'birth_year',
        'birthMonth': 'birth_month',
        'birthDay': 'birth_day',
        'birthCountry': 'birth_country',
        'birthState': 'birth_state',
        'birthCity': 'birth_city',
        'deathYear': 'death_year',
        'deathMonth': 'death_month',
        'deathDay': 'death_day',
        'deathCountry': 'death_country',
        'deathState': 'death_state',
        'deathCity': 'death_city',
        'nameFirst': 'name_first',
        'nameLast': 'name_last',
        'nameGiven': 'name_given',
        'finalGame': 'final_game',
        'retroID': 'retro_id',
        'bbrefID': 'bb_ref_id'
    }

    return new_names


def get_parser():
    """Args Description"""

    # current_year = datetime.datetime.today().year
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")

    return parser


def to_date(row, prefix):
    """Custom Parsing of birth and death dates"""
    y = row[prefix + '_year']
    m = row[prefix + '_month']
    d = row[prefix + '_day']

    # NaT if year is missing
    if pd.isna(y):
        return pd.NaT

    # if year present but month missing
    if pd.isna(m):
        m = 1

    # if year present but day missing
    if pd.isna(d):
        d = 1

    return pd.datetime(int(y), int(m), int(d))


def wrangle_people(p_raw, p_wrangled):
    if p_wrangled.joinpath('people.csv').exists():
        logging.info('Skipping wrangle of people - already performed')
        return

    os.chdir(p_raw)
    people = pd.read_csv('People.csv', parse_dates=['debut', 'finalGame'])

    people.rename(columns=get_fieldname_mapping(), inplace=True)
    people.columns = people.columns.str.lower()

    people['birth_date'] = people.apply(lambda x: to_date(x, 'birth'), axis=1)
    people['death_date'] = people.apply(lambda x: to_date(x, 'death'), axis=1)
    people = people.drop(
        ['birth_year', 'birth_month', 'birth_day',
         'death_year', 'death_month', 'death_day'], axis=1)

    msg = dh.df_info(people)
    logging.info('people\n{}'.format(msg))

    # persist as a csv file with data types
    os.chdir(p_wrangled)
    dh.to_csv_with_types(people, 'people.csv')


def wrangle_batting(p_raw, p_wrangled):
    if p_wrangled.joinpath('batting.csv').exists():
        logging.info('Skipping wrangle of batting - already performed')
        return

    os.chdir(p_raw)
    batting = pd.read_csv('Batting.csv')

    batting.rename(columns=get_fieldname_mapping(), inplace=True)
    batting.columns = batting.columns.str.lower()

    # downcast integers and convert float to Int64, if data permits
    batting = dh.optimize_df_dtypes(batting)

    msg = dh.df_info(batting)
    logging.info('batting\n{}'.format(msg))

    # persist with optimized datatypes
    os.chdir(p_wrangled)
    dh.to_csv_with_types(batting, 'batting.csv')


def wrangle_pitching(p_raw, p_wrangled):
    if p_wrangled.joinpath('pitching.csv').exists():
        logging.info('Skipping wrangle of pitching - already performed')
        return

    os.chdir(p_raw)
    pitching = pd.read_csv('Pitching.csv')

    pitching.rename(columns=get_fieldname_mapping(), inplace=True)
    pitching.columns = pitching.columns.str.lower()

    pitching = dh.optimize_df_dtypes(pitching)

    msg = dh.df_info(pitching)
    logging.info('pitching\n{}'.format(msg))

    # persist
    os.chdir(p_wrangled)
    dh.to_csv_with_types(pitching, 'pitching.csv')


def wrangle_fielding(p_raw, p_wrangled):
    if p_wrangled.joinpath('fielding.csv').exists():
        logging.info('Skipping wrangle of fielding - already performed')
        return

    os.chdir(p_raw)
    fielding = pd.read_csv('Fielding.csv')

    fielding.rename(columns=get_fieldname_mapping(), inplace=True)
    fielding.columns = fielding.columns.str.lower()

    # drop any column that is more than 90% null
    filt = fielding.isna().mean() > 0.90
    drop_cols = fielding.columns[filt]
    fielding = fielding.drop(drop_cols, axis=1)

    fielding = dh.optimize_df_dtypes(fielding)

    msg = dh.df_info(fielding)
    logging.info('fielding\n{}'.format(msg))

    # persist
    os.chdir(p_wrangled)
    dh.to_csv_with_types(fielding, 'fielding.csv')


def wrangle_teams(p_raw, p_wrangled):
    if p_wrangled.joinpath('teams.csv').exists():
        logging.info('Skipping wrangle of teams - already performed')
        return

    os.chdir(p_raw)
    teams = pd.read_csv('Teams.csv')

    teams.rename(columns=get_fieldname_mapping(), inplace=True)
    teams.columns = teams.columns.str.lower()

    teams = dh.optimize_df_dtypes(teams)

    msg = dh.df_info(teams)
    logging.info('teams\n{}'.format(msg))

    # persist
    os.chdir(p_wrangled)
    dh.to_csv_with_types(teams, 'teams.csv')


def main():
    """Perform the data transformations
    """
    parser = get_parser()
    args = parser.parse_args()

    if args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    # log to stdout
    logging.basicConfig(stream=sys.stdout, level=level, format='%(levelname)s: %(message)s')

    p_lahman_raw = Path(args.data_dir).joinpath('lahman/raw').resolve()
    p_lahman_wrangled = Path(args.data_dir).joinpath('lahman/wrangled').resolve()

    wrangle_people(p_lahman_raw, p_lahman_wrangled)
    wrangle_batting(p_lahman_raw, p_lahman_wrangled)
    wrangle_pitching(p_lahman_raw, p_lahman_wrangled)
    wrangle_fielding(p_lahman_raw, p_lahman_wrangled)
    wrangle_teams(p_lahman_raw, p_lahman_wrangled)


if __name__ == '__main__':
    main()
