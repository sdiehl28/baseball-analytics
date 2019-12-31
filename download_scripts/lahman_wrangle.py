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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_fieldname_mapping():
    """Dictionary of fieldnames that will be modified."""

    # It is easier to maintain fieldname mappings in a single location
    new_names = {
        'playerID': 'player_id',
        'yearID': 'year_id',
        'teamID': 'team_id',
        'lgID': 'lg_id',
        '2B': 'double',
        '3B': 'triple',
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
        'bbrefID': 'bb_ref_id',
        'park.key': 'park_key',
        'park.name': 'park_name',
        'park.alias': 'park_alias'
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
    parser.add_argument("--log", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")

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


def wrangle_basic(p_raw, p_wrangled, filename):
    """Basic Wrangle:  converts fieldnames, optimizes datatypes and persists data
    """
    filename_lower = str(filename).lower()
    wrangled_file = p_wrangled.joinpath(filename_lower)

    if wrangled_file.exists():
        logger.info(f'Skipping wrangle of {filename} - already performed')
        return

    os.chdir(p_raw)
    df = pd.read_csv(filename)

    df.rename(columns=get_fieldname_mapping(), inplace=True)
    df.columns = df.columns.str.lower()

    # downcast integers and convert float to Int64, if data permits
    dh.optimize_df_dtypes(df)

    msg = dh.df_info(df)
    logger.info('{}\n{}'.format(filename, msg))

    # persist with optimized datatypes
    os.chdir(p_wrangled)
    dh.to_csv_with_types(df, wrangled_file)


def wrangle_people(p_raw, p_wrangled):
    if p_wrangled.joinpath('people.csv').exists():
        logger.info('Skipping wrangle of People.csv - already performed')
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
    logger.info('people\n{}'.format(msg))

    # persist as a csv file with data types
    os.chdir(p_wrangled)
    dh.to_csv_with_types(people, 'people.csv')


def wrangle_fielding(p_raw, p_wrangled):
    if p_wrangled.joinpath('fielding.csv').exists():
        logger.info('Skipping wrangle of Fielding.csv - already performed')
        return

    os.chdir(p_raw)
    fielding = pd.read_csv('Fielding.csv')

    fielding.rename(columns=get_fieldname_mapping(), inplace=True)
    fielding.columns = fielding.columns.str.lower()

    # drop any column that is more than 90% null
    filt = fielding.isna().mean() > 0.90
    if filt.any():
        drop_cols = fielding.columns[filt]
        logger.warning(f'Cols > 90% missing being dropped: {" ".join(drop_cols)}')
        fielding.drop(drop_cols, axis=1, inplace=True)

    dh.optimize_df_dtypes(fielding)

    msg = dh.df_info(fielding)
    logger.info('fielding\n{}'.format(msg))

    # persist
    os.chdir(p_wrangled)
    dh.to_csv_with_types(fielding, 'fielding.csv')


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

    p_lahman_raw = Path(args.data_dir).joinpath('lahman/raw').resolve()
    p_lahman_wrangled = Path(args.data_dir).joinpath('lahman/wrangled').resolve()

    wrangle_people(p_lahman_raw, p_lahman_wrangled)
    wrangle_fielding(p_lahman_raw, p_lahman_wrangled)

    wrangle_basic(p_lahman_raw, p_lahman_wrangled, 'Batting.csv')
    wrangle_basic(p_lahman_raw, p_lahman_wrangled, 'Pitching.csv')
    wrangle_basic(p_lahman_raw, p_lahman_wrangled, 'Teams.csv')
    wrangle_basic(p_lahman_raw, p_lahman_wrangled, 'Salaries.csv')
    wrangle_basic(p_lahman_raw, p_lahman_wrangled, 'Parks.csv')


if __name__ == '__main__':
    main()
