#!/usr/bin/env python

"""Run all scripts"""

__author__ = 'Stephen Diehl'

import argparse
import sys
import subprocess


def get_parser():
    """Args Description"""

    # current_year = datetime.datetime.today().year
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')

    return parser


def run_cmd(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for line in proc.stdout:
        sys.stdout.buffer.write(line)
        sys.stdout.buffer.flush()


def main():
    parser = get_parser()
    args = parser.parse_args()
    data_dir = f'--data-dir={args.data_dir}'

    print('Running lahman_download:')
    cmd = ['./lahman_download.py', '-v', '--log=INFO', data_dir]
    run_cmd(cmd)

    print('Running lahman_wrangle:')
    cmd = ['./lahman_wrangle.py', '-v', '--log=INFO', data_dir]
    run_cmd(cmd)

    print('Running retrosheet_download:')
    cmd = ['./retrosheet_download.py', '-v', '--log=INFO', data_dir]
    run_cmd(cmd)

    print('Running retrosheet_parse:')
    cmd = ['./retrosheet_parse.py', '-v', '--log=INFO', data_dir]
    run_cmd(cmd)

    print('Running retrosheet_wrangle:')
    cmd = ['./retrosheet_wrangle.py', '-v', '--log=INFO', data_dir]
    run_cmd(cmd)

    print('All Scripts have run.')
    print('Run "pytest -v --runslow" at command line.')


if __name__ == '__main__':
    main()
