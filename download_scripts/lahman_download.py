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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_parser():
    """Args Description"""

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")
    parser.add_argument("--log", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")

    return parser


def mk_dirs(data_dir):
    """Make data directories"""
    p_lahman = Path(data_dir) / 'lahman'
    p_lahman_raw = p_lahman / 'raw'
    p_lahman_wrangled = p_lahman / 'wrangled'

    # create directories from these path objects
    p_lahman_raw.mkdir(parents=True, exist_ok=True)
    p_lahman_wrangled.mkdir(parents=True, exist_ok=True)

    msg = " ".join(os.listdir(p_lahman))
    logger.info(f'{p_lahman} contents: {msg}')


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

    if not Path(zip_filename).is_file():
        logger.info('Downloading Data ...')

        url = 'https://github.com/chadwickbureau/baseballdatabank/archive/master.zip'
        r = requests.get(url)
        r.raise_for_status()
        with open(zip_filename, 'wb') as f:
            f.write(r.content)

        # unzip it
        with zipfile.ZipFile(zip_filename, "r") as zip_ref:
            zip_ref.extractall('.')


def reorg_files(raw_dir):
    """move the unzipped files to the raw directory and remove the extract directory"""
    os.chdir(raw_dir)

    if not Path('People.csv').is_file():
        unzip_dir = raw_dir / 'baseballdatabank-master' / 'core'

        # move the unzipped csv files to the current working directory
        for root, dirs, files in os.walk(unzip_dir):
            for file in files:
                shutil.move(root + '/' + file, '.')

        # rm the extract directory
        shutil.rmtree('baseballdatabank-master')

    msg = '\n'.join(os.listdir('.'))
    logger.info(f'{raw_dir} contents:\n {msg}')


def main():
    """Download and Unzip Lahman Data to {data_dir}/lahman/raw"""
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

    data_dir = Path(args.data_dir)
    mk_dirs(data_dir)

    raw_dir = data_dir / 'lahman/raw'
    raw_dir = raw_dir.resolve()
    download_data(raw_dir)
    reorg_files(raw_dir)

    logger.info('Finished')


if __name__ == '__main__':
    main()
