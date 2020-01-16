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
        filename = '../wrangled/event.csv.gz'
    else:
        raise ValueError(f'Unrecognized parser: {parser}')

    dh.to_csv_with_types(df, filename)
    logger.info(f'{parser} data persisted')


def main():
    """Parse the data and organize the results.
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

    p_data = Path(args.data_dir).resolve()
    if p_data.joinpath('retrosheet', 'collected', 'player_game.csv.gz').exists() and \
       p_data.joinpath('retrosheet', 'collected', 'game.csv.gz').exists() and \
       p_data.joinpath('retrosheet', 'wrangled', 'event.csv.gz').exists():
        logger.info('Skipping collecting -- already performed')
        return

    p_data_parsed = p_data.joinpath('retrosheet/parsed')
    p_data_collected = p_data.joinpath('retrosheet/collected')

    # create directories, if they do not exist
    p_data_parsed.mkdir(parents=True, exist_ok=True)
    p_data_collected.mkdir(parents=True, exist_ok=True)

    collect_parsed_files(p_data_parsed, p_data_collected, 'cwevent', args.use_datatypes)
    collect_parsed_files(p_data_parsed, p_data_collected, 'cwdaily', args.use_datatypes)
    collect_parsed_files(p_data_parsed, p_data_collected, 'cwgame', args.use_datatypes)


if __name__ == '__main__':
    main()
