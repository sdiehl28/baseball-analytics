import pytest
import os
import subprocess
from pathlib import Path
import zipfile


@pytest.fixture(scope="session")
def download_data():
    """Will download data, if it does not already exist."""
    cmd = ['python', './lahman_download.py', '--data-dir', './test_data']
    subprocess.run(cmd, shell=False)

    cmd = ['python', './retrosheet_download.py', '--data-dir', './test_data',
           '--start-year', '2017', '--end-year', '2019']
    subprocess.run(cmd, shell=False)

    return Path('./test_data')


def test_lahman_download(download_data):
    data_dir = download_data
    lahman_dir = data_dir.joinpath('lahman')
    wrangled_dir = lahman_dir.joinpath('wrangled')
    raw_dir = lahman_dir.joinpath('raw')

    assert lahman_dir.exists()
    assert wrangled_dir.exists()
    assert raw_dir.exists()

    # 2 directories and 1 file
    assert len(list(lahman_dir.iterdir())) == 3

    # zip from master branch of https://github.com/chadwickbureau/baseballdatabank
    zipfilename = raw_dir.joinpath('baseballdatabank-master.zip')
    assert zipfilename.exists()

    zipped = zipfile.ZipFile(zipfilename)
    zip_core_files = [file for file in zipped.namelist()
                      if file.startswith('baseballdatabank-master/core/') and
                      file.endswith('.csv')]

    # each csv file in the zipfile should be in raw_dir
    assert len(list(raw_dir.glob('*.csv'))) == len(zip_core_files)


def test_retrosheet_download(download_data):
    data_dir = download_data
    retrosheet_dir = data_dir.joinpath('retrosheet')
    wrangled_dir = retrosheet_dir.joinpath('wrangled')
    raw_dir = retrosheet_dir.joinpath('raw')

    assert retrosheet_dir.exists()
    assert wrangled_dir.exists()
    assert raw_dir.exists()
