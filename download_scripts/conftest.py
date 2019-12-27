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


@pytest.fixture(scope='session')
def player_game(data_dir):
    # depending upon the amount of data, it could take 30 seconds to decompress player_game.csv.gz
    filename = data_dir / 'retrosheet' / 'wrangled' / 'player_game.csv.gz'
    player_game = dh.from_csv_with_types(filename)
    return player_game
