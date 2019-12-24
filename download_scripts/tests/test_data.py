import pytest
import os
import sys
import zipfile
import pandas as pd

from .. import data_helper as dh


def test_python_version():
    assert sys.version_info.major == 3
    assert sys.version_info.minor >= 7


def test_lahman_download(data_dir):
    lahman_dir = data_dir / 'lahman'
    raw_dir = lahman_dir / 'raw'
    wrangled_dir = lahman_dir / 'wrangled'

    assert lahman_dir.is_dir()
    assert wrangled_dir.is_dir()
    assert raw_dir.is_dir()

    # 2 directories and 1 file
    assert len(list(lahman_dir.iterdir())) == 3

    # zip from master branch of https://github.com/chadwickbureau/baseballdatabank
    zipfilename = raw_dir.joinpath('baseballdatabank-master.zip')
    assert zipfilename.is_file()

    zipped = zipfile.ZipFile(zipfilename)
    zip_core_files = [file for file in zipped.namelist()
                      if file.startswith('baseballdatabank-master/core/') and
                      file.endswith('.csv')]

    # each csv file in the zipfile should be in raw_dir
    assert len(list(raw_dir.glob('*.csv'))) == len(zip_core_files)


def test_retrosheet_download(data_dir):
    """Verify 2017 thru 2019 were downloaded and unzipped."""
    retrosheet_dir = data_dir / 'retrosheet'
    raw_dir = retrosheet_dir / 'raw'
    wrangled_dir = retrosheet_dir / 'wrangled'

    assert retrosheet_dir.is_dir()
    assert wrangled_dir.is_dir()
    assert raw_dir.is_dir()

    zip2017 = raw_dir.joinpath('2017eve.zip')
    zip2018 = raw_dir.joinpath('2018eve.zip')
    zip2019 = raw_dir.joinpath('2019eve.zip')

    assert zip2017.exists()
    assert zip2018.exists()
    assert zip2019.exists()

    # should be same number of files in raw_dir as in zipfile
    files_2017 = [file for file in raw_dir.glob('*2017*') if not file.name.endswith('.zip')]
    zipped = zipfile.ZipFile(zip2017)
    assert len(files_2017) == len(zipped.namelist())

    files_2018 = [file for file in raw_dir.glob('*2018*') if not file.name.endswith('.zip')]
    zipped = zipfile.ZipFile(zip2018)
    assert len(files_2018) == len(zipped.namelist())

    files_2019 = [file for file in raw_dir.glob('*2019*') if not file.name.endswith('.zip')]
    zipped = zipfile.ZipFile(zip2019)
    assert len(files_2019) == len(zipped.namelist())


def test_lahman_people_pkey(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'people.csv'

    # check for duplicate IDs
    people = dh.from_csv_with_types(filename)
    assert dh.is_unique(people, ['player_id'])  # lahman player id
    assert dh.is_unique(people, ['retro_id'], ignore_null=True)  # retrosheet player id


def test_lahman_fielding_pkey(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'fielding.csv'

    # check for duplicate IDs
    fielding = dh.from_csv_with_types(filename)
    assert dh.is_unique(fielding, ['player_id', 'year_id', 'stint', 'team_id', 'pos'])


def test_lahman_batting_pkey(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'batting.csv'

    # check for duplicate IDs
    batting = dh.from_csv_with_types(filename)
    assert dh.is_unique(batting, ['player_id', 'year_id', 'stint', 'team_id'])


def test_lahman_pitching_pkey(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'pitching.csv'

    # check for duplicate IDs
    pitching = dh.from_csv_with_types(filename)
    assert dh.is_unique(pitching, ['player_id', 'year_id', 'stint', 'team_id'])


def test_lahman_salaries_pkey(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'salaries.csv'

    # check for duplicate IDs
    salaries = dh.from_csv_with_types(filename)
    assert dh.is_unique(salaries, ['player_id', 'year_id', 'team_id'])


def test_lahman_teams_pkey(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'teams.csv'

    # check for duplicate IDs
    teams = dh.from_csv_with_types(filename)
    assert dh.is_unique(teams, ['team_id', 'year_id'])  # lahman team_id
    assert dh.is_unique(teams, ['team_id_retro', 'year_id'])  # retrosheet team_id


def test_lahman_parks_pkey(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'parks.csv'

    # check for duplicate IDs
    parks = dh.from_csv_with_types(filename)
    assert dh.is_unique(parks, ['park_key'])

    # park_name is not unique
    # assert dh.is_unique(parks, ['park_name']


def test_optimize_df():
    df = pd.DataFrame(dh.get_dtype_range())
    dh.optimize_df_dtypes(df)
    assert (df.dtypes.values == df.columns.values).all()


def test_rw_with_types(data_dir):
    dtype_range = dh.get_dtype_range()
    df = pd.DataFrame(dtype_range)
    dtypes_orig = df.dtypes

    dh.optimize_df_dtypes(df)
    dh.to_csv_with_types(df, data_dir / 'tmp.csv.gz')
    df = dh.from_csv_with_types(data_dir / 'tmp.csv.gz')

    assert (df.dtypes == list(dtype_range.keys())).all()
    assert not (df.dtypes == dtypes_orig).all()

    assert (data_dir / 'tmp.csv.gz').is_file()
    assert (data_dir / 'tmp_types.csv').is_file()
    os.remove(data_dir / 'tmp.csv.gz')
    os.remove(data_dir / 'tmp_types.csv')


def test_player_game_id_values(player_game):
    filt = player_game['home_fl'] == 0
    player_game['home_team_id'] = player_game['team_id']
    player_game.loc[filt, 'home_team_id'] = player_game.loc[filt, 'opponent_id']

    assert (player_game['game_id'] == player_game['home_team_id'] +
            player_game['game_dt'].astype(str) + player_game['game_ct'].astype(str)).all()


@pytest.mark.skip(reason="data must be cleaned before this test passes")
def test_player_game_pkey(data_dir):
    filename = data_dir / 'retrosheet' / 'collected' / 'player_game.csv.gz'

    player_game = dh.from_csv_with_types(filename)
    assert dh.is_unique(player_game, ['player_id', 'game_id'])
