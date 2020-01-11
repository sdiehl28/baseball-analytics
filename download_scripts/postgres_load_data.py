#!/usr/bin/env python

"""Load Wrangled data into Postgres"""

__author__ = 'Stephen Diehl'

import os
import sys
from pathlib import Path
import argparse
import logging
import csv
from io import StringIO

from sqlalchemy import create_engine

import data_helper as dh

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


# This improves df.to_sql() write speed by a couple orders of magnitude!
# This method was copied verbatim from:
# https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql-method
# Alternative to_sql() *method* for DBs that support COPY FROM
def psql_insert_copy(table, conn, keys, data_iter):
    # gets a DBAPI connection that can provide a cursor
    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        s_buf = StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)

        columns = ', '.join('"{}"'.format(k) for k in keys)
        if table.schema:
            table_name = '{}.{}'.format(table.schema, table.name)
        else:
            table_name = table.name

        sql = 'COPY {} ({}) FROM STDIN WITH CSV'.format(
            table_name, columns)
        cur.copy_expert(sql=sql, file=s_buf)


def create_and_load_table(engine, prefix, filename, pkey=None):
    table = prefix + filename.name.split('.')[0]
    logger.info(f'{table} loading ...')

    # read with optimized Pandas data types
    df = dh.from_csv_with_types(filename)

    # compute optimized database data types
    db_dtypes = dh.optimize_db_dtypes(df)

    # drop table and its dependencies (e.g. primary key constraint)
    engine.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
    df.to_sql(table, engine, index=False, dtype=db_dtypes, method=psql_insert_copy)

    # add primary key constraint
    if pkey:
        pkeys_str = ', '.join(pkey)
        sql = f'ALTER TABLE {table} ADD PRIMARY KEY ({pkeys_str})'
        engine.execute(sql)

    # rows added
    rs = engine.execute(f'SELECT COUNT(*) from {table}')
    result = rs.fetchall()
    rows = result[0][0]

    logger.info(f'{table} added with {rows} rows')


def load_lahman_tables(engine, data_dir):
    lahman_data = data_dir.joinpath('lahman/wrangled')

    create_and_load_table(engine, 'lahman_', lahman_data / 'people.csv', ['player_id'])
    sql = 'ALTER TABLE lahman_people ADD CONSTRAINT retro_player_unique UNIQUE (retro_id)'
    engine.execute(sql)

    create_and_load_table(engine, 'lahman_', lahman_data / 'batting.csv',
                          ['player_id', 'year', 'stint'])
    create_and_load_table(engine, 'lahman_', lahman_data / 'battingpost.csv',
                          ['player_id', 'year', 'round'])
    create_and_load_table(engine, 'lahman_', lahman_data / 'pitching.csv',
                          ['player_id', 'year', 'stint'])
    create_and_load_table(engine, 'lahman_', lahman_data / 'pitchingpost.csv',
                          ['player_id', 'year', 'round'])
    create_and_load_table(engine, 'lahman_', lahman_data / 'fielding.csv',
                          ['player_id', 'year', 'stint', 'pos'])
    create_and_load_table(engine, 'lahman_', lahman_data / 'fieldingpost.csv',
                          ['player_id', 'year', 'round', 'pos'])
    create_and_load_table(engine, 'lahman_', lahman_data / 'parks.csv',
                          ['park_key'])
    create_and_load_table(engine, 'lahman_', lahman_data / 'salaries.csv',
                          ['player_id', 'year', 'team_id'])
    create_and_load_table(engine, 'lahman_', lahman_data / 'teams.csv',
                          ['team_id', 'year'])
    sql = 'ALTER TABLE lahman_teams ADD CONSTRAINT retro_team_unique UNIQUE (team_id_retro, year)'
    engine.execute(sql)


def load_retrosheet_tables(engine, data_dir):
    retro_data = data_dir.joinpath('retrosheet/wrangled')

    create_and_load_table(engine, 'retro_', retro_data / 'batting.csv.gz',
                          ['player_id', 'game_id'])
    sql = """ALTER TABLE retro_batting
    ADD CONSTRAINT batting_player_id
    FOREIGN KEY(player_id)
    REFERENCES lahman_people(retro_id)
    """
    engine.execute(sql)
    create_and_load_table(engine, 'retro_', retro_data / 'pitching.csv.gz',
                          ['player_id', 'game_id'])
    sql = """ALTER TABLE retro_pitching
    ADD CONSTRAINT pitching_player_id
    FOREIGN KEY(player_id)
    REFERENCES lahman_people(retro_id)
    """
    engine.execute(sql)
    create_and_load_table(engine, 'retro_', retro_data / 'fielding.csv.gz',
                          ['player_id', 'game_id', 'pos'])
    sql = """ALTER TABLE retro_fielding
    ADD CONSTRAINT fielding_player_id
    FOREIGN KEY(player_id)
    REFERENCES lahman_people(retro_id)
    """
    engine.execute(sql)

    create_and_load_table(engine, 'retro_', retro_data / 'game.csv.gz',
                          ['game_id'])
    create_and_load_table(engine, 'retro_', retro_data / 'team_game.csv.gz',
                          ['team_id', 'game_id'])
    sql = 'ALTER TABLE retro_team_game ADD YEAR integer'
    engine.execute(sql)
    sql = """UPDATE retro_team_game 
    SET YEAR = CAST(DATE_PART('year', game_start_dt) AS integer)
    """
    engine.execute(sql)
    sql = """ALTER TABLE retro_team_game
    ADD CONSTRAINT team_id FOREIGN KEY (team_id, year) 
    REFERENCES lahman_teams (team_id_retro, year)
    """
    engine.execute(sql)

def main():
    """Load the data in Postgres.
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

    # Get the user and password from the environment (rather than hardcoding it)
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')

    # avoid putting passwords directly in code
    connect_str = f'postgresql://{db_user}:{db_pass}@localhost:5432/baseball'

    # for distinction between engine.execute() and engine.connect().execute() see:
    # https://stackoverflow.com/questions/34322471/sqlalchemy-engine-connection-and-session-difference#answer-42772654
    engine = create_engine(connect_str)

    data_dir = Path('../data')
    load_lahman_tables(engine, data_dir)
    load_retrosheet_tables(engine, data_dir)

    logger.info('Finished')


if __name__ == '__main__':
    main()
