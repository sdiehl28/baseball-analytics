#!/usr/bin/env python

"""Download and Unzip Retrosheet Data to {data_dir}/retrosheet/raw

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
    p_retrosheet_raw = data_dir / 'retrosheet/raw'
    p_retrosheet_wrangled = data_dir / 'retrosheet/wrangled'

    # create directories from these path objects
    p_retrosheet_raw.mkdir(parents=True, exist_ok=True)
    p_retrosheet_wrangled.mkdir(parents=True, exist_ok=True)


def download_data(raw_dir):
    """download and unzip retrosheet event files"""

    os.chdir(raw_dir)

    # download most recent Retrosheet data
    # most recent data is from chadwickbureau on github.
    zip_filename = 'retrosheet-master.zip'

    if not Path(zip_filename).is_file():
        logger.info('Downloading >200 MB of Data ...')

        url = 'https://github.com/chadwickbureau/retrosheet/archive/master.zip'
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

    unzip_dir = raw_dir / 'retrosheet-master'

    # move the subdirectories up one directory
    for dir in os.listdir(unzip_dir):
        shutil.move(unzip_dir.joinpath(dir).as_posix(), '.')

    # rm the extract directory
    shutil.rmtree('retrosheet-master')


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

    data_dir = Path(args.data_dir)
    mk_dirs(data_dir)

    raw_dir = (data_dir / 'retrosheet/raw').resolve()
    download_data(raw_dir)
    reorg_files(raw_dir)


if __name__ == '__main__':
    main()
