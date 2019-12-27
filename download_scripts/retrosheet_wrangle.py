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

import pandas as pd

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
    lahman_people_fn = p_retrosheet_collected.parent.parent / 'lahman/wrangled/people.csv'
    lahman_people = dh.from_csv_with_types(lahman_people_fn)

    lahman_teams_fn = p_retrosheet_collected.parent.parent / 'lahman/wrangled/teams.csv'
    lahman_teams = dh.from_csv_with_types(lahman_teams_fn)

    # add player_id from Lahman to make joins on players easier
    # retrosheet.player_game JOIN lahman.people ON player_id = retro_id
    player_game = pd.merge(player_game, lahman_people[['player_id', 'retro_id']],
                           left_on='player_id', right_on='retro_id',
                           suffixes=['', '_lahman'])

    # the retro_id from Lahman is not needed
    player_game.drop('retro_id', axis=1, inplace=True)

    # move the new player_id_lahman column to be after player_id
    player_game = dh.move_column_after(player_game, 'player_id', 'player_id_lahman')

    # add year_id to player_game (for use with Lahman teams)
    player_game['year_id'] = player_game['game_dt'] // 10000
    player_game = dh.move_column_after(player_game, 'game_dt', 'year_id')

    # add team_id from Lahman to make joins on teams easier
    # r.player_game JOIN l.teams ON r.year_id = l.year_id AND r.team_id = l.team_id_retro
    player_game = pd.merge(player_game, lahman_teams[['team_id', 'year_id', 'team_id_retro']],
                           left_on=['year_id', 'team_id'],
                           right_on=['year_id', 'team_id_retro'],
                           suffixes=['', '_lahman'])

    # the team retro_id from Lahman is not needed
    player_game.drop('team_id_retro', axis=1, inplace=True)

    # move the new team_id_lahman column to be after team_id
    player_game = dh.move_column_after(player_game, 'team_id', 'team_id_lahman')

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
