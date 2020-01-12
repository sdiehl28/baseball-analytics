"""Fixtures for Data Consistency Testing

   Data Consistency Testing is for the year 1974 through 2019 inclusive.
"""
import pytest
from pathlib import Path
from . import data_helper as dh


def pytest_addoption(parser):
    parser.addoption(
        "--data-dir", action='store', default="../data", type=str, help="baseball data directory"
    )
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return

    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(scope='session')
def data_dir(request):
    return Path(request.config.getoption("--data-dir"))


# @pytest.fixture(scope='session')
# def player_game(data_dir):
#     # depending upon the amount of data, it could take 30 seconds to decompress player_game.csv.gz
#     filename = data_dir / 'retrosheet' / 'collected' / 'player_game.csv.gz'
#     player_game = dh.from_csv_with_types(filename)
#     return player_game


@pytest.fixture(scope='session')
def team_game(data_dir):
    filename = data_dir / 'retrosheet' / 'wrangled' / 'team_game.csv.gz'
    team_game = dh.from_csv_with_types(filename)
    team_game = team_game.query('1974 <= game_start_dt.dt.year <= 2019')
    return team_game


@pytest.fixture(scope='session')
def game(data_dir):
    filename = data_dir / 'retrosheet' / 'wrangled' / 'game.csv.gz'
    game = dh.from_csv_with_types(filename)
    game = game.query('1974 <= game_start_dt.dt.year <= 2019')
    return game


@pytest.fixture(scope='session')
def batting(data_dir):
    filename = data_dir / 'retrosheet' / 'wrangled' / 'batting.csv.gz'
    batting = dh.from_csv_with_types(filename)
    batting = batting.query('1974 <= game_start_dt.dt.year <= 2019')
    return batting


@pytest.fixture(scope='session')
def pitching(data_dir):
    filename = data_dir / 'retrosheet' / 'wrangled' / 'pitching.csv.gz'
    pitching = dh.from_csv_with_types(filename)
    pitching = pitching.query('1974 <= game_start_dt.dt.year <= 2019')
    return pitching


@pytest.fixture(scope='session')
def fielding(data_dir):
    filename = data_dir / 'retrosheet' / 'wrangled' / 'fielding.csv.gz'
    fielding = dh.from_csv_with_types(filename)
    fielding = fielding.query('1974 <= game_start_dt.dt.year <= 2019')
    return fielding


@pytest.fixture(scope='session')
def lahman_batting(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'batting.csv'
    batting = dh.from_csv_with_types(filename)
    batting = batting.query('1974 <= year <= 2019')
    return batting


@pytest.fixture(scope='session')
def lahman_pitching(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'pitching.csv'
    pitching = dh.from_csv_with_types(filename)
    pitching = pitching.query('1974 <= year <= 2019')
    return pitching


@pytest.fixture(scope='session')
def lahman_fielding(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'fielding.csv'
    fielding = dh.from_csv_with_types(filename)
    fielding = fielding.query('1974 <= year <= 2019')
    return fielding


@pytest.fixture(scope='session')
def lahman_teams(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'teams.csv'
    teams = dh.from_csv_with_types(filename)
    teams = teams.query('1974 <= year <= 2019')
    return teams


@pytest.fixture(scope='session')
def lahman_people(data_dir):
    filename = data_dir / 'lahman' / 'wrangled' / 'people.csv'
    return dh.from_csv_with_types(filename)
