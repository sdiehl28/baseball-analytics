import pandas as pd
import numpy as np

import os
from pathlib import Path

from sqlalchemy import create_engine

import data_helper as dh


def create_and_load_lahman_table(conn, filename, pkey=None):
    lahman_table = 'lahman_' + filename.name.split('.')[0]
    print(f'{lahman_table:<15s} loading ...')

    # read in with optimized Pandas data types
    df = dh.from_csv_with_types(filename)

    # compute optimized database data types
    dtypes = dh.optimize_db_dtypes(df)

    """df.to_sql automatically creates a table with good but not optimal data types,
    hence the use of dh.optimize_db_dtypes()
    
    Note that df.to_sql(if_exists='replace') replaces the *data*, not the table.  This
    will not cause column data types to change, so drop the table first.
    """
    conn.execute(f'DROP TABLE IF EXISTS {lahman_table} CASCADE')
    df.to_sql(lahman_table, conn, index=False, dtype=dtypes)

    # add primary key constraint
    if pkey:
        pkeys_str = ', '.join(pkey)
        sql = f'ALTER TABLE {lahman_table} ADD PRIMARY KEY ({pkeys_str})'
        conn.execute(sql)

    # rows added
    rs = conn.execute(f'SELECT COUNT(*) from {lahman_table}')
    result = rs.fetchall()
    rows = result[0][0]

    print(f'{lahman_table} added with {rows} rows')


def main():
    # Get the user and password from the environment (rather than hardcoding it)
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')

    # avoid putting passwords directly in code
    connect_str = f'postgresql://{db_user}:{db_pass}@localhost:5432/baseball'

    # connect
    conn = create_engine(connect_str)

    data_dir = Path('../data')
    lahman_data = data_dir.joinpath('lahman/wrangled').resolve()

    create_and_load_lahman_table(conn, lahman_data / 'people.csv', ['player_id'])
    sql = 'ALTER TABLE lahman_people ADD CONSTRAINT retro_player_unique UNIQUE (retro_id)'
    conn.execute(sql)

    create_and_load_lahman_table(conn, lahman_data / 'batting.csv',
                                 ['player_id', 'year_id', 'stint'])
    create_and_load_lahman_table(conn, lahman_data / 'battingpost.csv',
                                 ['player_id', 'year_id', 'round'])
    create_and_load_lahman_table(conn, lahman_data / 'pitching.csv',
                                 ['player_id', 'year_id', 'stint'])
    create_and_load_lahman_table(conn, lahman_data / 'pitchingpost.csv',
                                 ['player_id', 'year_id', 'round'])
    create_and_load_lahman_table(conn, lahman_data / 'fielding.csv',
                                 ['player_id', 'year_id', 'stint', 'pos'])
    create_and_load_lahman_table(conn, lahman_data / 'fieldingpost.csv',
                                 ['player_id', 'year_id', 'round', 'pos'])
    create_and_load_lahman_table(conn, lahman_data / 'parks.csv',
                                 ['park_key'])
    create_and_load_lahman_table(conn, lahman_data / 'salaries.csv',
                                 ['player_id', 'year_id', 'team_id'])
    create_and_load_lahman_table(conn, lahman_data / 'teams.csv',
                                 ['team_id', 'year_id'])
    sql = 'ALTER TABLE lahman_teams ADD CONSTRAINT retro_team_unique UNIQUE (team_id_retro, year_id)'
    conn.execute(sql)

    retrosheet_data = data_dir.joinpath('retrosheet/wrangled').resolve()


if __name__ == '__main__':
    main()
