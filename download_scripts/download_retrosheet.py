#!/usr/bin/env python

"""Download and Unzip Retrosheet Data to {data_dir}/retrosheet/raw"""

__author__ = 'Stephen Diehl'

import os
import glob
import shutil
import argparse
import datetime
import wget
from pathlib import Path
import zipfile


def get_parser():
    """Args Description"""

    # current_year = datetime.datetime.today().year
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')
    parser.add_argument("--start-year", type=int, help="start year", default='1955')
    parser.add_argument("--end-year", type=int, help="end year", default='2019')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")

    return parser


def mk_dirs(data_dir, verbose):
    """Make data directories"""
    p_retrosheet = Path(data_dir).joinpath('retrosheet')
    p_retrosheet_raw = p_retrosheet.joinpath('raw')
    p_retrosheet_wrangled = p_retrosheet.joinpath('wrangled')

    # create directories from these path objects
    p_retrosheet_raw.mkdir(parents=True, exist_ok=True)
    p_retrosheet_wrangled.mkdir(parents=True, exist_ok=True)

    if verbose:
        dirs = os.listdir(p_retrosheet)
        print('Retrosheet Data Directories')
        print(f'{p_retrosheet}/{dirs[0]}')
        print(f'{p_retrosheet}/{dirs[1]}')

    return p_retrosheet_raw.resolve()


def download_data(raw_dir, start_year, end_year, verbose):
    """download and unzip retrosheet event files

    Note: prior to 1955, sacrafice flies were not recorded.
    """
    os.chdir(raw_dir)
    for year in range(start_year, end_year + 1):
        # download each event file, if it doesn't exist locally
        filename = f'{year}eve.zip'
        path = Path(filename)
        if not path.exists():
            try:
                print(f'Downloading data for {year}')
                url = f'http://www.retrosheet.org/events/{year}eve.zip'
                wget.download(url)
            except Exception:
                print(f'{year} data not available')
                break

        # unzip each zip file, if its contents don't exist locally
        # {year}BOS.EVA is in all zip files
        filename = f'{year}BOS.EVA'
        path = Path(filename)
        if not path.exists():
            filename = f'{year}eve.zip'
            with zipfile.ZipFile(filename, "r") as zip_ref:
                zip_ref.extractall(".")

    if verbose:
        # list the 2019 files
        ros_files = sorted(glob.glob('*2019.ROS'))
        eva_files = sorted(glob.glob('2019*.EVA'))
        evn_files = sorted(glob.glob('2019*.EVN'))
        team_files = glob.glob('TEAM2019')
        print('2019 ROS files\n', *ros_files, sep=' ')
        print('2019 EVA files\n', *eva_files, sep=' ')
        print('2019 EVN files\n', *evn_files, sep=' ')
        print('2019 TEAM files\n', *team_files, sep=' ')


def main():
    """Perform the actions
    """
    # adding command line argument
    parser = get_parser()
    args = parser.parse_args()
    raw_dir = mk_dirs(args.data_dir, args.verbose)
    download_data(raw_dir, args.start_year, args.end_year, args.verbose)
    # reorg_files(raw_dir, args.verbose)


if __name__ == '__main__':
    main()
