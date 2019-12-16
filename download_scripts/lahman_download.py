#!/usr/bin/env python

"""Download and Unzip Lahman Data to {data_dir}/lahman/raw

Will not download data if it has already been downloaded.
"""

__author__ = 'Stephen Diehl'

import os
import shutil
import argparse
import requests
from pathlib import Path
import zipfile
import logging
import sys


def get_parser():
    """Args Description"""

    # current_year = datetime.datetime.today().year
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")

    return parser


def mk_dirs(data_dir):
    """Make data directories"""
    p_lahman = Path(data_dir).joinpath('lahman')
    p_lahman_raw = p_lahman.joinpath('raw')
    p_lahman_wrangled = p_lahman.joinpath('wrangled')

    # create directories from these path objects
    p_lahman_raw.mkdir(parents=True, exist_ok=True)
    p_lahman_wrangled.mkdir(parents=True, exist_ok=True)

    msg = " ".join(os.listdir(p_lahman))
    logging.info(f'{p_lahman} files: {msg}')

    return p_lahman_raw.resolve()


def download_data(raw_dir):
    """download and unzip Lahman zip file"""
    os.chdir(raw_dir)

    # download most recent data dictionary (accurate for 2019)
    url = 'http://www.seanlahman.com/files/database/readme2017.txt'
    dd_filename = '../readme2017.txt'
    if not Path(dd_filename).is_file():
        r = requests.get(url)
        r.raise_for_status()
        with open(dd_filename, 'wb') as f:
            f.write(r.content)

    # download most recent Lahman data
    # most recent data is not from www.seanlahman.com.  It is from chadwickbureau on github.
    zip_filename = 'baseballdatabank-master.zip'
    baseball_zip = raw_dir.joinpath(zip_filename)

    if not baseball_zip.is_file():
        logging.info('Downloading Data ...')

        url = 'https://github.com/chadwickbureau/baseballdatabank/archive/master.zip'
        r = requests.get(url)
        r.raise_for_status()
        with open(zip_filename, 'wb') as f:
            f.write(r.content)

        # unzip it
        with zipfile.ZipFile(zip_filename, "r") as zip_ref:
            zip_ref.extractall('.')

    msg = ' '.join(os.listdir())
    logging.info(f'{raw_dir} contents: {msg}')


def reorg_files(raw_dir):
    """move the unzipped files to the raw directory and remove the extract directory"""
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

    msg = ' '.join(os.listdir())
    logging.info(f'{raw_dir} contents: {msg}')


def main():
    """Download and Unzip Lahman Data to {data_dir}/lahman/raw"""
    parser = get_parser()
    args = parser.parse_args()

    if args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    # log to stdout
    logging.basicConfig(stream=sys.stdout, level=level, format='%(levelname)s: %(message)s')

    raw_dir = mk_dirs(args.data_dir)
    download_data(raw_dir)
    reorg_files(raw_dir)


if __name__ == '__main__':
    main()
