#!/usr/bin/env python

"""Collect parsed event files"""

__author__ = 'Stephen Diehl'

import argparse
import sys
from pathlib import Path
import os
import glob
import pandas as pd
import data_helper as dh
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_parser():
    """Args Description"""

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")
    parser.add_argument("--use-datatypes", help="use precomputed datatypes", action="store_true")
    parser.add_argument("--log", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")

    return parser


def collect_parsed_files(parse_dir, collect_dir, parser, use_datatypes):
    """Collect all parsed files and optimize datatypes.
    """

    os.chdir(parse_dir)
    # read the augmented files, not the ones created by cwevent
    if parser == 'cwevent':
        dailyfiles = glob.glob(f'{parser}*_plus.csv')
    else:
        dailyfiles = glob.glob(f'{parser}*.csv')
    dailyfiles.sort()

    logger.info(f'Collecting {len(dailyfiles)} {parser} parsed csv files into single dataframe ...')

    if use_datatypes:
        # this can save gigabytes of RAM by using precomputed datatypes
        logger.info('Using precomputed data types')
        if parser == 'cwdaily':
            filename = '../player_game_types.csv'
        elif parser == 'cwgame':
            filename = '../game_types.csv'
        elif parser == 'cwevent':
            filename = '../event_types.csv'
        else:
            raise ValueError(f'Unrecognized parser: {parser}')

        dates, dtypes = dh.read_types(filename)
        dtypes = {key.upper(): value for key, value in dtypes.items()}

        df = pd.concat((pd.read_csv(f, parse_dates=dates, dtype=dtypes) for f in dailyfiles),
                       ignore_index=True, copy=False)
        logger.info(f'Optimized Memory Usage:   {dh.mem_usage(df)}')
    else:
        # this could use twice the RAM required to hold the DataFrame
        df = pd.concat((pd.read_csv(f) for f in dailyfiles), ignore_index=True, copy=False)

        logger.info(f'Unoptimized Memory Usage: {dh.mem_usage(df)}')
        logger.info('Optimizing Data Types to reduce memory ...')

        # for cwdaily, optimize_df_dtypes reduces the size of the dataframe by a factor of 3
        dh.optimize_df_dtypes(df)
        logger.info(f'Optimized Memory Usage:   {dh.mem_usage(df)}')

    # convert to lower case
    df.columns = df.columns.str.lower()

    # drop any column that is more than 99% null
    filt = df.isna().mean() > 0.99
    if filt.any():
        drop_cols = df.columns[filt]
        logger.warning(f'Cols > 99% missing being dropped: {" ".join(drop_cols)}')
        df.drop(drop_cols, axis=1, inplace=True)

    # persist optimized dataframe
    # gzip chosen over xy because this runs on client computer and gzip is faster
    logger.info('persisting dataframe using compression - this could take several minutes ...')
    os.chdir(collect_dir)
    if parser == 'cwdaily':
        filename = 'player_game.csv.gz'
    elif parser == 'cwgame':
        filename = 'game.csv.gz'
    elif parser == 'cwevent':  # was wrangled in parser to save RAM, write to wrangled dir
        filename = 'event.csv.gz'
    else:
        raise ValueError(f'Unrecognized parser: {parser}')

    dh.to_csv_with_types(df, filename)
    logger.info(f'{parser} data persisted')


def augment_event_files(p_data_parsed):
    """Augment event data

    cwevent does not produce a boolean or int for the following values:
    'so', 'sb', 'cs', 'bk', 'bb', 'ibb', 'hbp', 'xi', 'single', 'double', 'triple', 'hr'
    Extract these from event_tx and h_cd

    The advantage of creating these fields is:
     1) groupby (game,team) to sum values and compare with cwgame for data consistency check
     2) some play-by-play analysis is easier

    This method is in retrosheet_collect.py rather than retrosheet_wrangle.py, because
    many Gigs of RAM can be saved by collecting csv files with booleans instead of objects
    """
    os.chdir(p_data_parsed)
    files = p_data_parsed.glob('cwevent????.csv')
    for file in sorted(files):
        df = pd.read_csv(file)
        logger.info(f'Creating Augmented Event File: {file.name.split(".")[0]}_plus.csv')

        # change column names to lowercase
        cols = [col.lower() for col in df.columns]
        df.columns = cols

        # prepare to remove _fl from flag fields
        flag_fields = [col for col in df.columns if col.endswith('_fl')]
        new_names = [col[:-3] for col in flag_fields]

        # convert 'T' to True/False
        # a bool takes 8 times less memory than the object 'T'
        df[new_names] = df[flag_fields].applymap(lambda s: s == 'T')
        df.drop(columns=flag_fields, inplace=True)

        # use "better" names
        names = {'event_outs_ct': 'outs', 'err_ct': 'e', 'event_runs_ct': 'r',
                 'bat_home_id': 'home_half', 'pa_new': 'pa', 'bat_team_id': 'team_id',
                 'fld_team_id': 'opponent_team_id'}
        df = df.rename(columns=names)

        df['so'] = df['event_tx'].str.contains(r'^K')
        df['sb'] = df['event_tx'].str.count('SB')  # counts multiple stolen bases on one play
        df['cs'] = df['event_tx'].str.count('CS')  # counts multiple cs on one play
        df['bk'] = df['event_tx'].str.contains('BK')

        # 'I' not preceded by 'D' or 'B' or '/' and not followed by 'N'
        df['ibb'] = df['event_tx'].str.contains(r'(?<![DB\/])I(?!N)')

        # 'W' not preceded by 'I' or 'D' and not followed by 'P'
        df['bb'] = df['event_tx'].str.contains(r'(?<![ID])W(?!P)')

        # by definition, bb includes ibb
        df['bb'] |= df['ibb']

        df['hbp'] = df['event_tx'].str.contains('HP')

        # batter my reach base on interference by pitcher or catcher or 1st baseman
        df['xi'] = df['event_tx'].str.contains(r'C/E(?:1|2|3)')

        df['single'] = df['h_cd'] == 1
        df['double'] = df['h_cd'] == 2
        df['triple'] = df['h_cd'] == 3
        df['hr'] = df['h_cd'] == 4
        df['h'] = df['h_cd'] > 0

        df.to_csv(f'{file.name.split(".")[0]}_plus.csv', index=False)


def main():
    """Collect the CSV files."""
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

    p_data = Path(args.data_dir).resolve()
    p_data_parsed = p_data.joinpath('retrosheet/parsed')
    p_data_collected = p_data.joinpath('retrosheet/collected')

    # create directories, if they do not exist
    p_data_parsed.mkdir(parents=True, exist_ok=True)
    p_data_collected.mkdir(parents=True, exist_ok=True)

    event_files = list(p_data_parsed.glob('cwevent*.csv'))
    if event_files:
        if p_data.joinpath('retrosheet', 'collected', 'event.csv.gz').exists():
            logger.info('Skipping cwevent collection -- already performed')
        else:
            augment_event_files(p_data_parsed)
            collect_parsed_files(p_data_parsed, p_data_collected, 'cwevent', args.use_datatypes)

    if p_data.joinpath('retrosheet', 'collected', 'player_game.csv.gz').exists():
        logger.info('Skipping cwdaily collection -- already performed')
    else:
        collect_parsed_files(p_data_parsed, p_data_collected, 'cwdaily', args.use_datatypes)

    if p_data.joinpath('retrosheet', 'collected', 'game.csv.gz').exists():
        logger.info('Skipping cwgame collection -- already performed')
    else:
        collect_parsed_files(p_data_parsed, p_data_collected, 'cwgame', args.use_datatypes)


if __name__ == '__main__':
    main()
