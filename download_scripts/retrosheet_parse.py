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

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")

    return parser


def parse_event_files(raw_dir, parser, parser_args):
    """Parse ALL downloaded event data"""
    os.chdir(raw_dir)

    years = glob.glob('TEAM*')
    years = sorted([year[4:] for year in years])

    for year in years:
        files = sorted(glob.glob(f'{year}*.EV*'))
        first = True

        logging.info(f'{parser} parsing {len(files)} teams for {year} ...')

    for file in files:
        out = f'../parsed/{parser}{year}.csv'
        if first:
            # print header using -n
            cmd = f'cwdaily -f 0-153 -n -y {year} {file}'
            cmd = cmd.split(' ')

            # overwrite any existing file
            with open(out, "w+") as outfile:
                result = subprocess.run(cmd, shell=False, stdout=outfile, stderr=subprocess.DEVNULL)
            first = False


def process_cwdaily(raw_dir):
    """Parse all downloaded event data into player stats per game.
    """
    os.chdir(raw_dir)

    years = glob.glob('TEAM*')
    years = sorted([year[4:] for year in years])

    for year in years:
        files = sorted(glob.glob(f'{year}*.EV*'))
        first = True

        logging.info(f'cwdaily parsing {len(files)} teams for {year} ...')

        for file in files:
            out = f'../parsed/daily{year}.csv'
            if first:
                # print header using -n
                cmd = f'cwdaily -f 0-153 -n -y {year} {file}'
                cmd = cmd.split(' ')

                # overwrite any existing file
                with open(out, "w+") as outfile:
                    result = subprocess.run(cmd, shell=False, stdout=outfile, stderr=subprocess.DEVNULL)
                first = False
            else:
                # no header
                cmd = f'cwdaily -f 0-153 -y {year} {file}'
                cmd = cmd.split(' ')

                # append to existing file
                with open(out, "a+") as outfile:
                    result = subprocess.run(cmd, shell=False, stdout=outfile, stderr=subprocess.DEVNULL)


def process_cwgame(raw_dir):
    """Parse all downloaded event data into team stats per game.
    """
    os.chdir(raw_dir)

    years = glob.glob('TEAM*')
    years = sorted([year[4:] for year in years])

    for year in years:
        files = sorted(glob.glob(f'{year}*.EV*'))
        first = True

        logging.info(f'cwgame parsing {len(files)} teams for {year} ...')

        for file in files:
            out = f'../parsed/game{year}.csv'
            if first:
                # print header using -n
                cmd = f'cwgame -f 0-83 -x 0-94 -n -y {year} {file}'
                cmd = cmd.split(' ')

                # overwrite any existing file
                with open(out, "w+") as outfile:
                    result = subprocess.run(cmd, shell=False, stdout=outfile, stderr=subprocess.DEVNULL)
                first = False
            else:
                # no header
                cmd = f'cwgame -f 0-83 -x 0-94 -y {year} {file}'
                cmd = cmd.split(' ')

                # append to existing file
                with open(out, "a+") as outfile:
                    result = subprocess.run(cmd, shell=False, stdout=outfile, stderr=subprocess.DEVNULL)


def collect_cwdaily_files(parse_dir, collect_dir):
    """Collect all parsed cwdaily files and optimize datatypes.
    """

    os.chdir(parse_dir)
    dailyfiles = glob.glob('daily*.csv')
    dailyfiles.sort()

    # Warning: player_game could be a few gigabytes in size
    # These operations could take a few minutes

    logging.info(f'Collecting {len(dailyfiles)} parsed csv files into single dataframe ...')
    player_game = pd.concat((pd.read_csv(f) for f in dailyfiles))

    player_game = player_game.reset_index(drop=True)
    player_game.columns = player_game.columns.str.lower()
    mem_usage = bb.mem_usage(player_game)
    logging.info(f'Unoptimized Memory Usage: {bb.mem_usage(player_game)}')
    logging.info('Optimizing ...')

    # this uses about 1/3rd the memory for the same data
    player_game = bb.optimize_df_dtypes(player_game)
    logging.info(f'Optimized Memory Usage:   {bb.mem_usage(player_game)}')

    # persist optimized dataframe
    # gzip chosen over xy because this runs on client computer and gzip is faster
    logging.info('persisting dataframe with compression ...')
    os.chdir(collect_dir)
    bb.to_csv_with_types(player_game, 'player_game.csv.gz')
    logging.info('cwgame data persisted')


def collect_cwgame_files(parse_dir, collect_dir):
    """Collect all parsed cwgame files and optimize datatypes.
    """
    pass


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

    # process_cwdaily(p_data_raw, args.verbose)
    collect_cwdaily_files(p_data_parsed, p_data_collected)

    # process_cwgame(p_data_raw, args.verbose)
    collect_cwgame_files(p_data_parsed, p_data_collected)


if __name__ == '__main__':
    main()
