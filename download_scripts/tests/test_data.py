import pytest
import os
import sys
import subprocess
from pathlib import Path
import zipfile


@pytest.fixture(scope="session")
def download_data():
    """Will download data, if it does not already exist."""

    # change to the download_script directory, if we are not already there
    if 'download_scripts' in [file.name for file in Path(os.getcwd()).iterdir()]:
        os.chdir('./download_scripts')

    cmd = ['python', './lahman_download.py', '--data-dir', './test_data']
    subprocess.run(cmd, shell=False)

    cmd = ['python', './retrosheet_download.py', '--data-dir', './test_data',
           '--start-year', '2017', '--end-year', '2019']
    subprocess.run(cmd, shell=False)

    return Path('./test_data')


def test_python_version():
    assert sys.version_info.major == 3
    assert sys.version_info.minor >= 7


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

