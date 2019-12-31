#!/usr/bin/env python

"""Use the Retrosheet parsers to generate their Data Dictionaries."""

__author__ = 'Stephen Diehl'

import csv
import subprocess
import os
from pathlib import Path
import io
import re
import argparse


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


def get_cwdaily_values(description):
    """Get cwdaily field descriptions"""
    cwdaily_values = []
    for line in io.StringIO(description):

        # if the line starts with a number
        if re.match(r'^\d+', line):
            tmp = line.rstrip()[8:]

            if ':' in tmp:
                key, value = tmp.split(':')
                value = value.strip()
            else:
                value = tmp.strip()
            cwdaily_values.append(value)

    return cwdaily_values


def get_cwgame_values(description):
    """get cwgame field descriptions"""
    cwgame_values = []
    for line in io.StringIO(description):

        # if the line starts with a number
        if re.match(r'^\d+', line):
            tmp = line.rstrip()[8:]

            if ':' in tmp:
                key, value = tmp.split(':')
                value = value.strip()
            else:
                value = tmp.strip()
            cwgame_values.append(value)

    return cwgame_values


def main():
    """Generate Data Dictionary from cwdaily and cwgame parsers"""
    check_for_retrosheet_parsers()

    parser = get_parser()
    args = parser.parse_args()

    p_data = Path(args.data_dir).resolve()
    p_data_raw = p_data.joinpath('retrosheet/raw')
    os.chdir(p_data_raw)

    # TODO allow this to work with any event file found in raw directory
    if not Path('2019LAN.EVN').is_file():
        raise FileNotFoundError('retrosheet data must be downloaded first')

    args = ['cwdaily', '-f', '0-153', '-n', '-y', '2019', '2019LAN.EVN']
    result = subprocess.run(args, shell=False, text=True, capture_output=True)

    # get header row
    cwdaily_keys = next(csv.reader(io.StringIO(result.stdout)))

    args = ['cwgame', '-f', '0-83', '-x', '0-94', '-n', '-y', '2019', '2019LAN.EVN']
    result = subprocess.run(args, shell=False, text=True, capture_output=True)

    # get header row
    cwgame_keys = next(csv.reader(io.StringIO(result.stdout)))

    args = ['cwdaily', '-f', '0-153', '-d']
    result = subprocess.run(args, shell=False, text=True, capture_output=True)

    # stderr not stdout
    cwdaily_values = get_cwdaily_values(result.stderr)

    args = ['cwgame', '-f', '0-83', '-x', '0-94', '-d']
    result = subprocess.run(args, shell=False, text=True, capture_output=True)

    # stderr not stdout
    cwgame_values = get_cwgame_values(result.stderr)

    assert len(cwdaily_keys) == len(cwdaily_values)
    assert len(cwgame_keys) == len(cwgame_values)
    cwdaily_dict = dict(zip(cwdaily_keys, cwdaily_values))
    cwgame_dict = dict(zip(cwgame_keys, cwgame_values))

    p_retrosheet = p_data.joinpath('retrosheet')
    os.chdir(p_retrosheet)
    with open('cwdaily_datadictionary.txt', 'w') as fh:
        for key, value in cwdaily_dict.items():
            fh.write(f'{key} = {value}\n')

    with open('cwgame_datadictionary.txt', 'w') as fh:
        for key, value in cwgame_dict.items():
            fh.write(f'{key} = {value}\n')


if __name__ == '__main__':
    main()
