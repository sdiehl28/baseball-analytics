#!/usr/bin/env python

"""Wrangle Lahman Data from {data_dir}/lahman/raw to {data_dir}/lahman/wrangled"""

__author__ = 'Stephen Diehl'

import argparse
import subprocess
from pathlib import Path
import os
import glob


def get_parser():
    """Args Description"""

    # current_year = datetime.datetime.today().year
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")

    return parser


def check_for_retrosheet_parsers():
    """Check that parsers can be executed."""
    p1 = subprocess.run(['cwdaily', '-h'], shell=False, capture_output=True)
    if p1.returncode != 0:
        raise FileNotFoundError('could not execute cwdaily')

    p1 = subprocess.run(['cwgame', '-h'], shell=False, capture_output=True)
    if p1.returncode != 0:
        raise FileNotFoundError('could not execute cwgame')


def process_cwdaily(year, verbose):
    """Parse event data into player stats per game.
    """
    files = glob.glob(f'{year}*.EV*')
    first = True

    if verbose:
        print(f'cwdaily parsing {len(files)} teams for {year} ...')

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


def main():
    """Parse the data.
    """
    check_for_retrosheet_parsers()

    parser = get_parser()
    args = parser.parse_args()

    p_data = Path(args.data_dir).resolve()
    p_data_raw = p_data.joinpath('retrosheet/raw')
    os.chdir(p_data_raw)

    process_cwdaily('2019', args.verbose)


if __name__ == '__main__':
    main()
