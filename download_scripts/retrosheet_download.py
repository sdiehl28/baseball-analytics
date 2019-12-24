#!/usr/bin/env python

"""Download and Unzip Retrosheet Data to {data_dir}/retrosheet/raw

Will not download data if it has already been downloaded.
"""

__author__ = 'Stephen Diehl'

import os
import glob
import argparse
import requests
from pathlib import Path
import zipfile
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_parser():
    """Args Description"""

    # current_year = datetime.datetime.today().year
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

    return parser


def mk_dirs(data_dir):
    """Make data directories"""
    p_retrosheet = Path(data_dir).joinpath('retrosheet')
    p_retrosheet_raw = p_retrosheet.joinpath('raw')
    p_retrosheet_wrangled = p_retrosheet.joinpath('wrangled')

    # create directories from these path objects
    p_retrosheet_raw.mkdir(parents=True, exist_ok=True)
    p_retrosheet_wrangled.mkdir(parents=True, exist_ok=True)

    msg = " ".join(os.listdir(p_retrosheet))
    logger.info(f'{p_retrosheet} contents: {msg}')

    return p_retrosheet_raw.resolve()


def download_data(raw_dir, start_year, end_year):
    """download and unzip retrosheet event files
    """

    os.chdir(raw_dir)
    for year in range(start_year, end_year + 1):
        # download each event file, if it doesn't exist locally
        filename = f'{year}eve.zip'
        path = Path(filename)
        if not path.exists():
            url = f'http://www.retrosheet.org/events/{year}eve.zip'
            logger.info(f'Downloading {url}')
            r = requests.get(url)
            r.raise_for_status()
            with open(filename, 'wb') as f:
                f.write(r.content)

        # unzip each zip file, if its contents don't exist locally
        # {year}BOS.EVA is in all zip files
        filename = f'{year}BOS.EVA'
        path = Path(filename)
        if not path.exists():
            filename = f'{year}eve.zip'
            with zipfile.ZipFile(filename, "r") as zip_ref:
                zip_ref.extractall(".")

    years = glob.glob('TEAM*')
    years = sorted([year[4:] for year in years])
    logger.info(f'Data downloaded for years: {years[0]} thru {years[-1]}')


def main():
    """Download Retrosheet Event Files
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

    raw_dir = mk_dirs(args.data_dir)
    download_data(raw_dir, args.start_year, args.end_year)


if __name__ == '__main__':
    main()
