import pytest
import os
import sys
import subprocess
from pathlib import Path
import zipfile
import pandas as pd
import numpy as np

from .. import data_helper as dh


@pytest.fixture(scope="session")
def download_data():
    """Runs Scripts

    Data is persisted so next time this fixture is run, it will run much faster.
    To recreate the test data, remove ./test_data
    """

    # relative paths are used so be sure we start in the right directory
    curr_dir = Path(os.getcwd())
    if curr_dir.joinpath('./download_scripts/data_helper.py').exists():
        os.chdir('./download_scripts')
    elif curr_dir.joinpath('../data_helper.py').exists():
        os.chdir('..')

    cmd = ['python', './lahman_download.py', '--data-dir', './test_data']
    subprocess.run(cmd, shell=False)

    cmd = ['python', './retrosheet_download.py', '--data-dir', './test_data',
           '--start-year', '2017', '--end-year', '2019']
    subprocess.run(cmd, shell=False)

    cmd = ['python', './lahman_wrangle.py', '--data-dir', './test_data']
    subprocess.run(cmd, shell=False)

    cmd = ['python', './retrosheet_parse.py', '--data-dir', './test_data']
    subprocess.run(cmd, shell=False)

    return Path('./test_data')


def test_python_version():
    assert sys.version_info.major == 3
    assert sys.version_info.minor >= 7


def test_lahman_download(download_data):
    data_dir = download_data
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


def test_retrosheet_download(download_data):
    data_dir = download_data
    retrosheet_dir = data_dir / 'retrosheet'
    raw_dir = retrosheet_dir / 'raw'
    wrangled_dir = retrosheet_dir / 'wrangled'

    assert retrosheet_dir.is_dir()
    assert wrangled_dir.is_dir()
    assert raw_dir.is_dir()

    # 3 event files were downloaded by the fixture
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


def test_lahman_people_pkey(download_data):
    data_dir = download_data
    filename = data_dir / 'lahman' / 'wrangled' / 'people.csv'

    # check for duplicate IDs
    people = dh.from_csv_with_types(filename)
    assert dh.is_unique(people, ['player_id'])  # lahman player id
    assert dh.is_unique(people, ['retro_id'], ignore_null=True)  # retrosheet player id


def test_lahman_fielding_pkey(download_data):
    data_dir = download_data
    filename = data_dir / 'lahman' / 'wrangled' / 'fielding.csv'

    # check for duplicate IDs
    fielding = dh.from_csv_with_types(filename)
    assert dh.is_unique(fielding, ['player_id', 'year_id', 'stint', 'team_id', 'pos'])


def test_lahman_batting_pkey(download_data):
    data_dir = download_data
    filename = data_dir / 'lahman' / 'wrangled' / 'batting.csv'

    # check for duplicate IDs
    batting = dh.from_csv_with_types(filename)
    assert dh.is_unique(batting, ['player_id', 'year_id', 'stint', 'team_id'])

def test_lahman_pitching_pkey(download_data):
    data_dir = download_data
    filename = data_dir / 'lahman' / 'wrangled' / 'pitching.csv'

    # check for duplicate IDs
    pitching = dh.from_csv_with_types(filename)
    assert dh.is_unique(pitching, ['player_id', 'year_id', 'stint', 'team_id'])

def test_lahman_salaries_pkey(download_data):
    data_dir = download_data
    filename = data_dir / 'lahman' / 'wrangled' / 'salaries.csv'

    # check for duplicate IDs
    salaries = dh.from_csv_with_types(filename)
    assert dh.is_unique(salaries, ['player_id', 'year_id', 'team_id'])

def test_lahman_teams_pkey(download_data):
    data_dir = download_data
    filename = data_dir / 'lahman' / 'wrangled' / 'teams.csv'

    # check for duplicate IDs
    teams = dh.from_csv_with_types(filename)
    assert dh.is_unique(teams, ['team_id', 'year_id'])  # lahman team_id
    assert dh.is_unique(teams, ['team_id_retro', 'year_id'])  # retrosheet team_id

def test_lahman_parks_pkey(download_data):
    data_dir = download_data
    filename = data_dir / 'lahman' / 'wrangled' / 'parks.csv'

    # check for duplicate IDs
    parks = dh.from_csv_with_types(filename)
    assert dh.is_unique(parks, ['park_key'])

    # park_name is not unique
    # assert dh.is_unique(parks, ['park_name']

def test_optimize_df():
    data = {'a': [1, 100, 1000], 'b':[0,1,0], 'c':[-1, 0, 1]}
    df = pd.DataFrame(data=data)

    df2 = df.copy()
    dh.optimize_df_dtypes(df)
    assert (df.dtypes.values == [np.uint16, np.uint8, np.int8]).all()

def test_rw_with_types(download_data):
    data_dir = download_data
    data = {'a': [1, 100, 1000], 'b':[0,1,0], 'c':[-1, 0, 1]}
    df = pd.DataFrame(data=data)

    df2 = df.copy()
    dh.optimize_df_dtypes(df)
    dh.to_csv_with_types(df, data_dir / 'tmp.csv.gz')
    df = dh.from_csv_with_types(data_dir / 'tmp.csv.gz')

    assert not (df.dtypes == df2.dtypes).all()
    assert (data_dir / 'tmp.csv.gz').is_file()
    assert (data_dir / 'tmp_types.csv').is_file()
    os.remove(data_dir / 'tmp.csv.gz')
    os.remove(data_dir / 'tmp_types.csv')

@pytest.mark.skip(reason="data must be cleaned before this test passes")
def test_player_game_pkey(download_data):
    data_dir = download_data
    filename = data_dir / 'retrosheet' / 'collected' / 'player_game.csv.gz'

    player_game = dh.from_csv_with_types(filename)
    assert dh.is_unique(player_game, ['game_id'])
    assert dh.is_unique(player_game, ['game_dt', 'game_ct', 'team_id'])