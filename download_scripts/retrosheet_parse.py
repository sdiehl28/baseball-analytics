#!/usr/bin/env python

"""Parse all event files in {data_dir}/retrosheet/raw and put result in {data_dir}/retrosheet/parsed"""

__author__ = 'Stephen Diehl'

import argparse
import subprocess
import sys
from pathlib import Path
import os
import glob
import logging
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_parser():
    """Args Description"""

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')

    # Some Key MLB Data Dates
    # 1955: sacrifice files, sacrifice bunts and intentional walks are recorded for the first time
    # 1969: divisional play begins
    # 1974: Retrosheet is missing no games from 1974 to present
    parser.add_argument("--start-year", type=int, help="start year", default='1955')

    # Retrosheet Data for 2019 became available in December 2019
    parser.add_argument("--end-year", type=int, help="end year", default='2019')

    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")
    parser.add_argument("--use-datatypes", help="use precomputed datatypes", action="store_true")
    parser.add_argument("--log", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")

    return parser


def check_for_retrosheet_parsers():
    """Check that parsers can be executed."""
    p1 = subprocess.run(['cwevent', '-h'], shell=False, capture_output=True)
    if p1.returncode != 0:
        raise FileNotFoundError('could not execute cwevent')

    p1 = subprocess.run(['cwdaily', '-h'], shell=False, capture_output=True)
    if p1.returncode != 0:
        raise FileNotFoundError('could not execute cwdaily')

    p1 = subprocess.run(['cwgame', '-h'], shell=False, capture_output=True)
    if p1.returncode != 0:
        raise FileNotFoundError('could not execute cwgame')


def parse_event_files(raw_dir, parse_dir, parser, fields, start_year, end_year):
    """Parse ALL downloaded event data"""
    os.chdir(raw_dir)

    for year in range(start_year, end_year + 1):
        files = sorted(glob.glob(f'{year}*.EV*'))
        first = True

        cmd = [parser]
        cmd.extend(fields.split(' '))

        logger.info(f'{parser} parsing {len(files)} teams for {year} ...')

        for file in files:
            out = f'{parse_dir.as_posix()}/{parser}{year}.csv'
            if first:
                # print csv header using -n
                cmd.append('-n')
                cmd.extend(['-y', str(year)])

                cmd_full = cmd + [file]
                logger.debug(f'{" ".join(cmd_full)}')

                # overwrite existing file if it exists
                with open(out, "w+") as outfile:
                    result = subprocess.run(cmd_full, shell=False, stdout=outfile, stderr=subprocess.DEVNULL)
                first = False

                # don't print csv header for subsequent teams in the same year
                cmd.remove('-n')
            else:
                cmd_full = cmd + [file]
                logger.debug(f'{" ".join(cmd_full)}')

                # append to existing file
                with open(out, "a+") as outfile:
                    result = subprocess.run(cmd_full, shell=False, stdout=outfile, stderr=subprocess.DEVNULL)


def augment_event_files(p_data_parsed, start_year, end_year):
    """Augment event data

    cwevent does not produce a flag for the following values:
    'so', 'sb', 'cs', 'bk', 'bb', 'ibb', 'hbp', 'xi', 'single', 'double', 'triple', 'hr'
    Extract a boolean column for each using event_tx and h_cd
    sb will be an integer representing the number of stolen bases on the play

    The advantage of using a flag is that groupby "half-inning" can sum boolean values
    to get the total per half-inning.  The above flags allow for comparison with cwgame.

    This method is in retrosheet_parse rather than retrosheet_wrangle, because it saves
    a lot of RAM in retrosheet_collect when processing the very large event files.
    """
    os.chdir(p_data_parsed)
    for year in range(start_year, end_year + 1):
        df = pd.read_csv(f'cwevent{year}.csv')
        logger.info(f'Creating Augmented Event File: cwevent{year}_plus.csv')

        cols = [col.lower() for col in df.columns]
        df.columns = cols

        flag_fields = [col for col in df.columns if col.endswith('_fl')]

        new_names = [col[:-3] for col in flag_fields]

        df[new_names] = df[flag_fields].applymap(lambda s: s == 'T')
        df.drop(columns=flag_fields, inplace=True)

        # use "better" names
        names = {'event_outs_ct': 'outs', 'err_ct': 'e', 'event_runs_ct': 'r', 'bat_home_id': 'home_half',
                 'pa_new': 'pa', 'bat_team_id': 'team_id', 'fld_team_id': 'opponent_team_id'}
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
        df['xi'] = df['event_tx'].str.contains(r'C/E(?:1|2|3)')

        df['single'] = df['h_cd'] == 1
        df['double'] = df['h_cd'] == 2
        df['triple'] = df['h_cd'] == 3
        df['hr'] = df['h_cd'] == 4
        df['h'] = df['h_cd'] > 0

        df.to_csv(f'cwevent{year}_plus.csv', index=False)


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

    if args.start_year > 1974:
        logger.WARNING('data consistency tests require start_year <= 1974')
        args.start_year = 1974

    if args.end_year < 2019:
        logger.WARNING('data consistency tests require end-year >= 2019')
        args.end_year = 2019

    check_for_retrosheet_parsers()

    p_data = Path(args.data_dir).resolve()

    p_data_raw = p_data.joinpath('retrosheet/raw/event/regular')
    p_data_parsed = p_data.joinpath('retrosheet/parsed')
    p_data_collected = p_data.joinpath('retrosheet/collected')

    if (p_data_parsed / 'cwdaily2019.csv').exists():
        logger.info('Skipping parsing -- already performed')
        return

    # create directories, if they do not exist
    p_data_parsed.mkdir(parents=True, exist_ok=True)
    p_data_collected.mkdir(parents=True, exist_ok=True)

    # there are too many rows to request all available fields
    parse_event_files(p_data_raw, p_data_parsed, 'cwevent',
                      '-f 0,2,3,8,9,10,14,29,36-42,44,45,51 -x 1,2,5,8,11,13,14,45,50,55',
                      args.start_year, args.end_year)

    augment_event_files(p_data_parsed, args.start_year, args.end_year)

    # all available fields are selected for cwdaily and cwgame
    parse_event_files(p_data_raw, p_data_parsed, 'cwdaily', '-f 0-153', args.start_year, args.end_year)
    parse_event_files(p_data_raw, p_data_parsed, 'cwgame', '-f 0-83 -x 0-94', args.start_year, args.end_year)


if __name__ == '__main__':
    main()
