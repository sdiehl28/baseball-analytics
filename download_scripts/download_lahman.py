#!/usr/bin/env python

"""Download and Unzip Lahman Data to {data_dir}/lahman/raw"""

__author__ = 'Stephen Diehl'

import os
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

    parser.add_argument("--data-dir", type=str, help="lahman download directory", default='../data')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")

    return parser


def mk_dirs(data_dir, verbose):
    """Make data directories"""
    p_lahman = Path(data_dir).joinpath('lahman')
    p_lahman_raw = p_lahman.joinpath('raw')
    p_lahman_wrangled = p_lahman.joinpath('wrangled')

    # create directories from these path objects
    p_lahman_raw.mkdir(parents=True, exist_ok=True)
    p_lahman_wrangled.mkdir(parents=True, exist_ok=True)

    if verbose:
        dirs = os.listdir(p_lahman)
        print('Data Directories')
        print(f'{p_lahman}/{dirs[0]}')
        print(f'{p_lahman}/{dirs[1]}')

    return p_lahman_raw.resolve()


def download_data(raw_dir, verbose):
    """download Lahman zip file"""
    os.chdir(raw_dir)
    baseball_zip = raw_dir.joinpath('baseballdatabank-master.zip')

    if not baseball_zip.is_file():
        if verbose:
            print('Downloading Data ...')

        url = 'https://github.com/chadwickbureau/baseballdatabank/archive/master.zip'
        wget.download(url)

        # unzip it
        with zipfile.ZipFile('baseballdatabank-master.zip', "r") as zip_ref:
            zip_ref.extractall()

    if verbose:
        dirs = os.listdir()
        print('files:', *dirs)


def reorg_files(raw_dir, verbose):
    """move the unzipped files to the current directory and remove the extract directory"""
    os.chdir(raw_dir)
    people_csv = raw_dir.joinpath('People.csv')

    if not people_csv.is_file():
        unzip_dir = raw_dir.joinpath('baseballdatabank-master/core')

        # move the unzipped csv files to the current working directory
        for root, dirs, files in os.walk(unzip_dir):
            for file in files:
                shutil.move(root + '/' + file, '.')

        # rm the extract directory
        shutil.rmtree('baseballdatabank-master')

    if verbose:
        files = os.listdir()
        print('files:', *files)

def main():
    """Perform the actions
    """
    # adding command line argument
    parser = get_parser()
    args = parser.parse_args()
    raw_dir = mk_dirs(args.data_dir, args.verbose)
    download_data(raw_dir, args.verbose)
    reorg_files(raw_dir, args.verbose)


if __name__ == '__main__':
    main()
