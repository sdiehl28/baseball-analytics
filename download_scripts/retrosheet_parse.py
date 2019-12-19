#!/usr/bin/env python

"""Parse all event files in {data_dir}/retrosheet/raw and put result in {data_dir}/retrosheet/parsed"""

__author__ = 'Stephen Diehl'

import argparse
import subprocess
import sys
from pathlib import Path
import os
import glob
import pandas as pd
import data_helper as dh
import logging


def get_parser():
    """Args Description"""

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # TODO: allow user to specify fields created by each parser
    # TODO: For example, no fielding attributes from cwdaily
    # TODO: For example, no starting lineup from cwgame
    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")
    parser.add_argument("-d", "--data-type", help="use precomputed datatypes", action="store_true")

    return parser


def parse_event_files(raw_dir, parser, fields):
    """Parse ALL downloaded event data"""
    os.chdir(raw_dir)

    years = glob.glob('TEAM*')
    years = sorted([year[4:] for year in years])

    for year in years:
        files = sorted(glob.glob(f'{year}*.EV*'))
        first = True

        cmd = [parser]
        cmd.extend(fields.split(' '))

        logging.info(f'{parser} parsing {len(files)} teams for {year} ...')

        for file in files:
            out = f'../parsed/{parser}{year}.csv'
            if first:
                # print header using -n
                # print csv header using -n
                cmd.append('-n')
                cmd.extend(['-y', year])

                cmd_full = cmd + [file]
                logging.info(f'{" ".join(cmd_full)}')

                # overwrite existing file if it exists
                with open(out, "w+") as outfile:
                    result = subprocess.run(cmd_full, shell=False, stdout=outfile, stderr=subprocess.DEVNULL)
                first = False

                # don't print csv header for subsequent teams in the same year
                cmd.remove('-n')
            else:
                cmd_full = cmd + [file]
                logging.info(f'{" ".join(cmd_full)}')

                # append to existing file
                with open(out, "a+") as outfile:
                    result = subprocess.run(cmd_full, shell=False, stdout=outfile, stderr=subprocess.DEVNULL)


def collect_parsed_files(parse_dir, collect_dir, parser, use_data_types):
    """Collect all parsed cwdaily files and optimize datatypes.
    """

    os.chdir(parse_dir)
    dailyfiles = glob.glob(f'{parser}*.csv')
    dailyfiles.sort()

    logging.info(f'Collecting {len(dailyfiles)} {parser} parsed csv files into single dataframe ...')

    if use_data_types:
        # this uses 3 time less memory for cwdaily but relies on precomputed data types
        logging.info('Using precomputed data types')
        if parser == 'cwdaily':
            filename = '../player_game_types.csv'
        elif parser == 'cwgame':
            filename = '../team_game_types.csv'
        else:
            raise ValueError(f'Unrecognized parser: {parser}')

        dates, dtypes = dh.read_types(filename)
        dtypes = {key.upper(): value for key, value in dtypes.items()}

        df = pd.concat((pd.read_csv(f, parse_dates=dates, dtype=dtypes) for f in dailyfiles), ignore_index=True,
                       copy=False)
        logging.info(f'Optimized Memory Usage:   {dh.mem_usage(df)}')
    else:
        # this could use twice the memory of the largest dataframe
        df = pd.concat((pd.read_csv(f) for f in dailyfiles), ignore_index=True, copy=False)

        logging.info(f'Unoptimized Memory Usage: {dh.mem_usage(df)}')
        logging.info('Optimizing Data Types to reduce memory ...')

        # for cwdaily, optimize_df_dtypes reduces the size of the dataframe by a factor of 3
        df = dh.optimize_df_dtypes(df)
        logging.info(f'Optimized Memory Usage:   {dh.mem_usage(df)}')

    df.columns = df.columns.str.lower()

    # persist optimized dataframe
    # gzip chosen over xy because this runs on client computer and gzip is faster
    logging.info('persisting dataframe using compression - this could take several minutes ...')
    os.chdir(collect_dir)
    if parser == 'cwdaily':
        filename = 'player_game.csv.gz'
    elif parser == 'cwgame':
        filename = 'team_game.csv.gz'
    else:
        raise ValueError(f'Unrecognized parser: {parser}')

    dh.to_csv_with_types(df, filename)
    logging.info(f'{parser} data persisted')


def main():
    """Parse the data and organize the results.
    """
    parser = get_parser()
    args = parser.parse_args()

    if args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    # log to stdout
    logging.basicConfig(stream=sys.stdout, level=level, format='%(levelname)s: %(message)s')

    p_data = Path(args.data_dir).resolve()
    if p_data.joinpath('retrosheet', 'collected', 'player_game.csv.gz').exists() and \
            p_data.joinpath('retrosheet', 'collected', 'team_game.csv.gz').exists():
        logging.info('Skipping parsing -- already performed')
        return

    p_data_raw = p_data.joinpath('retrosheet/raw')
    p_data_parsed = p_data.joinpath('retrosheet/parsed')
    p_data_collected = p_data.joinpath('retrosheet/collected')

    # create directories, if they do not exist
    p_data_parsed.mkdir(parents=True, exist_ok=True)
    p_data_collected.mkdir(parents=True, exist_ok=True)

    parse_event_files(p_data_raw, 'cwdaily', '-f 0-153')
    parse_event_files(p_data_raw, 'cwgame', '-f 0-83 -x 0-94')

    collect_parsed_files(p_data_parsed, p_data_collected, 'cwdaily', args.data_type)
    collect_parsed_files(p_data_parsed, p_data_collected, 'cwgame', args.data_type)


if __name__ == '__main__':
    main()
