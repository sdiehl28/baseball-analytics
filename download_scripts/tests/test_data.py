import pytest
import zipfile

__author__ = 'Stephen Diehl'

from .. import data_helper as dh


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
    """Verify data downloaded and unzipped."""
    retrosheet_dir = data_dir / 'retrosheet'
    raw_dir = retrosheet_dir / 'raw'
    wrangled_dir = retrosheet_dir / 'wrangled'

    assert retrosheet_dir.is_dir()
    assert wrangled_dir.is_dir()
    assert raw_dir.is_dir()

    teams = raw_dir.glob('TEAM*')
    years = sorted([team.name[4:] for team in teams])

    for year in years:
        zipdata = raw_dir.joinpath(f'{year}eve.zip')
        assert zipdata.exists()

        # should be same number of files in raw_dir as in zipfile
        files = [file for file in raw_dir.glob(f'*{year}*') if not file.name.endswith('.zip')]
        zipped = zipfile.ZipFile(zipdata)
        assert len(files) == len(zipped.namelist())


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


@pytest.mark.slow
def test_player_game_id_values(player_game):
    # note: test is not slow, but running the session fixture could take 30 seconds
    filt = player_game['home_fl'] == 0
    player_game['home_team_id'] = player_game['team_id']
    player_game.loc[filt, 'home_team_id'] = player_game.loc[filt, 'opponent_id']

    assert (player_game['game_id'] == player_game['home_team_id'] +
            player_game['game_dt'].astype(str) + player_game['game_ct'].astype(str)).all()


def test_batting_pkey(batting):
    assert dh.is_unique(batting, ['player_id', 'game_id'])


def test_pitching_pkey(pitching):
    assert dh.is_unique(pitching, ['player_id', 'game_id'])


def test_fielding_pkey(fielding):
    assert dh.is_unique(fielding, ['player_id', 'game_id', 'pos'])


def test_team_game_pkey(team_game):
    assert dh.is_unique(team_game, ['team_id', 'game_id'])


def test_game_pkey(game):
    assert dh.is_unique(game, ['game_id'])
