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
    parser.add_argument("--log", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")

    parser.add_argument("--run-cwevent", help="verbose output", action="store_true")
    parser.add_argument("--cwevent-fields", type=str, help="cwevent field specification",
                        default='-f 0,2,3,8,9,10,14,29,36-42,44,45,51,96 -x 1,2,5,8,11,13,14,45,50,55')

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
    """Parse raw Retrosheet data"""
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
        logger.warning('data consistency tests require start_year <= 1974')
        args.start_year = 1974

    if args.end_year < 2019:
        logger.warning('data consistency tests require end-year >= 2019')
        args.end_year = 2019

    check_for_retrosheet_parsers()

    p_data = Path(args.data_dir).resolve()

    p_data_raw = p_data.joinpath('retrosheet/raw/event/regular')
    p_data_parsed = p_data.joinpath('retrosheet/parsed')
    p_data_collected = p_data.joinpath('retrosheet/collected')

    # create directories, if they do not exist
    p_data_parsed.mkdir(parents=True, exist_ok=True)
    p_data_collected.mkdir(parents=True, exist_ok=True)

    # this selection of fields appears to support most play-by-play analysis
    if args.run_cwevent:
        if (p_data_parsed / 'cwevent2019.csv').exists():
            logger.info('Skipping cwevent parsing -- already performed')
        else:
            parse_event_files(p_data_raw, p_data_parsed, 'cwevent',
                              args.cwevent_fields, args.start_year, args.end_year)

    # request all available fields for cwdaily and cwgame
    if (p_data_parsed / 'cwdaily2019.csv').exists():
        logger.info('Skipping cwdaily parser -- already performed')
    else:
        parse_event_files(p_data_raw, p_data_parsed, 'cwdaily', '-f 0-153', args.start_year, args.end_year)

    if (p_data_parsed / 'cwgame2019.csv').exists():
        logger.info('Skipping cwgame parser -- already performed')
    else:
        parse_event_files(p_data_raw, p_data_parsed, 'cwgame', '-f 0-83 -x 0-94', args.start_year, args.end_year)


if __name__ == '__main__':
    main()
