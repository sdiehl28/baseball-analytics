#!/usr/bin/env python

"""Wrangle Lahman Data from {data_dir}/lahman/raw to {data_dir}/lahman/wrangled"""

__author__ = 'Stephen Diehl'

import pandas as pd

import io
import os
import argparse
from pathlib import Path
import baseball_functions as bb


# http://www.seanlahman.com/files/database/
# data dictionary: readme2017.txt

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


def wrangle_people(p_raw, p_wrangled, verbose):
    os.chdir(p_raw)
    people = pd.read_csv('People.csv', parse_dates=['debut', 'finalGame'])

    # convert column names from CamelCase to snake_case
    people.columns = [bb.convert_camel_case(name) for name in people.columns]

    people['birth_date'] = people.apply(lambda x: to_date(x, 'birth'), axis=1)
    people['death_date'] = people.apply(lambda x: to_date(x, 'death'), axis=1)
    people = people.drop(
        ['birth_year', 'birth_month', 'birth_day',
         'death_year', 'death_month', 'death_day'], axis=1)

    # df.info() goes to stdout by default, capture it
    buffer = io.StringIO()
    people.info(buf=buffer)
    if verbose:
        print('people\n', buffer.getvalue())

    # persist as a csv file with data types
    os.chdir(p_wrangled)
    bb.to_csv_with_types(people, 'people.csv')

    # verify that data type information was not lost
    df2 = bb.from_csv_with_types('people.csv')
    assert (df2.dtypes == people.dtypes).all()


def wrangle_batting(p_raw, p_wrangled, verbose):
    os.chdir(p_raw)
    batting = pd.read_csv('Batting.csv')

    # use same column names in both Lahman and Retrosheet
    new_names = {
        'playerID': 'player_id',
        'yearID': 'year_id',
        'stint': 'stint',
        'teamID': 'team_id',
        'lgID': 'lg_id',
        'G': 'g',
        'AB': 'ab',
        'R': 'r',
        'H': 'h',
        '2B': 'b_2b',
        '3B': 'b_3b',
        'HR': 'hr',
        'RBI': 'rbi',
        'SB': 'sb',
        'CS': 'cs',
        'BB': 'bb',
        'SO': 'so',
        'IBB': 'ibb',
        'HBP': 'hp',
        'SH': 'sh',
        'SF': 'sf',
        'GIDP': 'gdp'
    }
    batting = batting.rename(columns=new_names)

    # downcast integers and convert float to Int64, if data permits
    batting = bb.optimize_df_dtypes(batting)

    # df.info() goes to stdout by default, capture it
    buffer = io.StringIO()
    batting.info(buf=buffer)
    if verbose:
        print('batting\n', buffer.getvalue())

    # persist with optimized datatypes
    os.chdir(p_wrangled)
    bb.to_csv_with_types(batting, 'batting.csv')

    # verify that data type information was not lost
    df2 = bb.from_csv_with_types('batting.csv')
    assert (df2.dtypes == batting.dtypes).all()


def wrangle_pitching(p_raw, p_wrangled, verbose):
    os.chdir(p_raw)
    pitching = pd.read_csv('Pitching.csv')

    # use same column names in both Lahman and Retrosheet
    new_names = {
        'playerID': 'player_id',
        'yearID': 'year_id',
        'stint': 'sting',
        'teamID': 'team_id',
        'lgID': 'lg_id',
        'W': 'w',
        'L': 'l',
        'G': 'g',
        'GS': 'gs',
        'CG': 'cg',
        'SHO': 'sho',
        'SV': 'sv',
        'IPouts': 'ip_outs',
        'H': 'h',
        'ER': 'er',
        'HR': 'hr',
        'BB': 'bb',
        'SO': 'so',
        'BAOpp': 'ba_opp',
        'ERA': 'era',
        'IBB': 'ibb',
        'WP': 'wp',
        'HBP': 'hp',
        'BK': 'bk',
        'BFP': 'bfp',
        'GF': 'gf',
        'R': 'r',
        'SH': 'sh',
        'SF': 'sf',
        'GIDP': 'gdp'
    }

    pitching = pitching.rename(columns=new_names)
    pitching = bb.optimize_df_dtypes(pitching)

    # df.info() goes to stdout by default, capture it
    buffer = io.StringIO()
    pitching.info(buf=buffer)
    if verbose:
        print('pitching\n', buffer.getvalue())

    # persist
    os.chdir(p_wrangled)
    bb.to_csv_with_types(pitching, 'pitching.csv')

    # verify data type information was not lost
    df2 = bb.from_csv_with_types('pitching.csv')
    assert (df2.dtypes == pitching.dtypes).all()


def wrangle_fielding(p_raw, p_wrangled, verbose):
    os.chdir(p_raw)
    fielding = pd.read_csv('Fielding.csv')

    # use same column names in both Lahman and Retrosheet
    new_names = {
        'playerID': 'player_id',
        'yearID': 'year_id',
        'teamID': 'team_id',
        'lgID': 'lg_id',
        'POS': 'pos',
        'G': 'g',
        'GS': 'gs',
        'InnOuts': 'inn_outs',
        'PO': 'po',
        'A': 'a',
        'E': 'e',
        'DP': 'dp'
    }

    # there are non-field attributes in the field data
    # these can be identified by being mostly null
    # drop them
    filt = fielding.isna().mean() > 0.90
    drop_cols = fielding.columns[filt]
    fielding = fielding.drop(drop_cols, axis=1)

    fielding = fielding.rename(columns=new_names)
    fielding = bb.optimize_df_dtypes(fielding)

    # df.info() goes to stdout by default, capture it
    buffer = io.StringIO()
    fielding.info(buf=buffer)
    if verbose:
        print('fielding\n', buffer.getvalue())

    # persist
    os.chdir(p_wrangled)
    bb.to_csv_with_types(fielding, 'fielding.csv')

    # verify data type information was not lost
    df2 = bb.from_csv_with_types('fielding.csv')
    assert (df2.dtypes == fielding.dtypes).all()


def wrangle_teams(p_raw, p_wrangled, verbose):
    os.chdir(p_raw)
    teams = pd.read_csv('Teams.csv')

    new_names = {
        'yearID': 'year_id',
        'lgID': 'lg_id',
        'teamID': 'team_id',
        'franchID': 'franch_id',
        'divID': 'div_id',
        'Rank': 'rank',
        'G': 'g',
        'Ghome': 'g_home',
        'W': 'w',
        'L': 'l',
        'DivWin': 'div_win',
        'WCWin': 'wc_win',
        'LgWin': 'lg_win',
        'WSWin': 'ws_win',
        'R': 'r',
        'AB': 'ab',
        'H': 'h',
        '2B': 'b_2b',
        '3B': 'b_3b',
        'HR': 'hr',
        'BB': 'bb',
        'SO': 'so',
        'SB': 'sb',
        'CS': 'cs',
        'HBP': 'hbp',
        'SF': 'sf',
        'RA': 'ra',
        'ER': 'er',
        'ERA': 'era',
        'CG': 'cg',
        'SHO': 'sho',
        'SV': 'sv',
        'IPouts': 'ip_outs',
        'HA': 'ha',
        'HRA': 'hra',
        'BBA': 'bba',
        'SOA': 'soa',
        'E': 'e',
        'DP': 'dp',
        'FP': 'fp',
        'name': 'name',
        'park': 'park',
        'attendance': 'attendance',
        'BPF': 'bpf',
        'PPF': 'ppf',
        'teamIDBR': 'team_id_br',
        'teamIDlahman45': 'team_id_lahman45',
        'teamIDretro': 'team_id_retro',
    }

    teams = teams.rename(columns=new_names)
    teams = bb.optimize_df_dtypes(teams)

    # df.info() goes to stdout by default, capture it
    buffer = io.StringIO()
    teams.info(buf=buffer)
    if verbose:
        print('teams\n', buffer.getvalue())

    # persist
    os.chdir(p_wrangled)
    bb.to_csv_with_types(teams, 'teams.csv')

    # verify data type information was not lost
    df2 = bb.from_csv_with_types('teams.csv')
    assert (df2.dtypes == teams.dtypes).all()


def main():
    """Perform the data transformations
    """
    # adding command line argument
    parser = get_parser()
    args = parser.parse_args()

    p_lahman_raw = Path(args.data_dir).joinpath('lahman/raw').resolve()
    p_lahman_wrangled = Path(args.data_dir).joinpath('lahman/wrangled').resolve()

    wrangle_people(p_lahman_raw, p_lahman_wrangled, args.verbose)
    wrangle_batting(p_lahman_raw, p_lahman_wrangled, args.verbose)
    wrangle_pitching(p_lahman_raw, p_lahman_wrangled, args.verbose)
    wrangle_fielding(p_lahman_raw, p_lahman_wrangled, args.verbose)
    wrangle_teams(p_lahman_raw, p_lahman_wrangled, args.verbose)


if __name__ == '__main__':
    main()
