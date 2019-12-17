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
import baseball_functions as bb
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


def collect_cwdaily_files(parse_dir, collect_dir, use_data_types):
    """Collect all parsed cwdaily files and optimize datatypes.
    """

    os.chdir(parse_dir)
    dailyfiles = glob.glob('cwdaily*.csv')
    dailyfiles.sort()

    logging.info(f'Collecting {len(dailyfiles)} cwdaily parsed csv files into single dataframe ...')

    if use_data_types:
        logging.info('Using precomputed data types')
        filename_types = '../player_game_types.csv'
        dates, dtypes = bb.read_types(filename_types)

        player_game = pd.concat((pd.read_csv(f, parse_dates=dates, dtype=dtypes) for f in dailyfiles), ignore_index=True, copy=False)
        logging.info(f'Optimized Memory Usage:   {bb.mem_usage(player_game)}')
    else:
        # for cwdaily, for all fields, from 1955 thru 2019, player_game will be 5.2GB
        # pandas operations will require as least twice the size of cwdaily for RAM
        player_game = pd.concat((pd.read_csv(f) for f in dailyfiles), ignore_index=True, copy=False)

        logging.info(f'Unoptimized Memory Usage: {bb.mem_usage(player_game)}')
        logging.info('Optimizing Data Types to reduce memory ...')

        # for cwdaily, optimize_df_dtypes reduces the size of the dataframe by a factor of 3
        player_game = bb.optimize_df_dtypes(player_game)
        logging.info(f'Optimized Memory Usage:   {bb.mem_usage(player_game)}')

    player_game.columns = player_game.columns.str.lower()

    # persist optimized dataframe
    # gzip chosen over xy because this runs on client computer and gzip is faster
    logging.info('persisting dataframe using compression - this could take several minutes ...')
    os.chdir(collect_dir)
    bb.to_csv_with_types(player_game, 'player_game.csv.gz')
    logging.info('cwdaily data persisted')


def collect_cwgame_files(parse_dir, collect_dir, use_data_types):
    """Collect all parsed cwgame files and optimize datatypes.
    """
    os.chdir(parse_dir)
    dailyfiles = glob.glob('cwgame*.csv')
    dailyfiles.sort()

    logging.info(f'Collecting {len(dailyfiles)} cwgame parsed csv files into single dataframe ...')

    if use_data_types:
        logging.info('Using precomputed data types')
        filename_types = '../team_game_types.csv'
        types = pd.read_csv(filename_types).set_index('index').to_dict()
        dtypes = types['dtypes']
        dtypes = {key.upper(): value for key, value in dtypes.items()}

        dates = [key for key, value in dtypes.items() if value.startswith('datetime')]
        for field in dates:
            dtypes.pop(field)

        team_game = pd.concat((pd.read_csv(f, parse_dates=dates, dtype=dtypes) for f in dailyfiles),
                                ignore_index=True, copy=False)
        logging.info(f'Optimized Memory Usage:   {bb.mem_usage(team_game)}')
    else:
        team_game = pd.concat((pd.read_csv(f) for f in dailyfiles), ignore_index=True, copy=False)

        logging.info(f'Unoptimized Memory Usage: {bb.mem_usage(team_game)}')
        logging.info('Optimizing Data Types to reduce memory ...')

        # for cwdaily, optimize_df_dtypes reduces the size of the dataframe by a factor of 3
        team_game = bb.optimize_df_dtypes(team_game)
        logging.info(f'Optimized Memory Usage:   {bb.mem_usage(team_game)}')

    team_game.columns = team_game.columns.str.lower()

    # persist optimized dataframe
    # gzip chosen over xy because this runs on client computer and gzip is faster
    logging.info('persisting dataframe using compression - this could take several minutes ...')
    os.chdir(collect_dir)
    bb.to_csv_with_types(team_game, 'team_game.csv.gz')
    logging.info('cwgame data persisted')


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
    p_data_raw = p_data.joinpath('retrosheet/raw')
    p_data_parsed = p_data.joinpath('retrosheet/parsed')
    p_data_collected = p_data.joinpath('retrosheet/collected')

    # create directories, if they do not exist
    p_data_parsed.mkdir(parents=True, exist_ok=True)
    p_data_collected.mkdir(parents=True, exist_ok=True)

    # parse_event_files(p_data_raw, 'cwdaily', '-f 0-153')
    # parse_event_files(p_data_raw, 'cwgame', '-f 0-83 -x 0-94')

    collect_cwdaily_files(p_data_parsed, p_data_collected, args.data_type)
    collect_cwgame_files(p_data_parsed, p_data_collected, args.data_type)


if __name__ == '__main__':
    main()
