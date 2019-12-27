#!/usr/bin/env python

"""Wrangle Retrosheet Data from {data_dir}/retrosheet/raw to {data_dir}/retrosheet/wrangled

Wrangles: player per game and team per game data
"""

__author__ = 'Stephen Diehl'

import argparse
import re
from pathlib import Path
import logging
import sys
import data_helper as dh

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_parser():
    """Args Description"""

    # current_year = datetime.datetime.today().year
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--data-dir", type=str, help="baseball data directory", default='../data')
    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")
    parser.add_argument("--log", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level")

    return parser


def wrangle_player_per_game(p_retrosheet_collected, p_retrosheet_wrangled):
    logger.info('Reading player_game.csv.gz ...')
    filename = p_retrosheet_collected / 'player_game.csv.gz'
    player_game = dh.from_csv_with_types(filename)
    logger.info('player_game loaded')

    # Fix Duplicate Primary Key
    pkey = ['game_id', 'player_id']
    if not dh.is_unique(player_game, pkey):
        # if pkey is dup, sum the stat rows for the dups
        dups = player_game.duplicated(subset=pkey)
        df_dups = player_game.loc[dups, pkey]
        logger.warning(f'Dup PKey Found\n{df_dups.to_string()}')

        # player stat columns b_ for batter, p_ for pitcher, f_ for fielder
        stat_columns = [col for col in player_game.columns if re.search(r'^[bpf]_', col)]

        # sum all stat columns except the game column
        stat_columns.remove('b_g')

        player_game = dh.sum_stats_for_dups(player_game, pkey, stat_columns)

    # Remove appear_dt as it has same values as game_dt
    if (player_game['game_dt'] == player_game['appear_dt']).mean() > 0.999:
        player_game.drop('appear_dt', axis=1, inplace=True)

    # Add Lahman player_id to make joins with Lahman easier later
    # Under construction - 12/27/19
    lahman_people_fn = p_retrosheet_collected.parent.parent / 'lahman/wrangled/people.csv'
    lahman_people = dh.from_csv_with_types(lahman_people_fn)

    logger.info('Writing and compressing player_game.  This could take several minutes ...')
    dh.to_csv_with_types(player_game, p_retrosheet_wrangled / 'player_game.csv.gz')
    logger.info('player_game written.')


def main():
    """Perform the data transformations
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

    p_retrosheet_collected = Path(args.data_dir).joinpath('retrosheet/collected').resolve()
    p_retrosheet_wrangled = Path(args.data_dir).joinpath('retrosheet/wrangled').resolve()

    wrangle_player_per_game(p_retrosheet_collected, p_retrosheet_wrangled)


if __name__ == '__main__':
    main()
