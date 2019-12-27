import os
import sys
import pandas as pd

__author__ = 'Stephen Diehl'

from .. import data_helper as dh


def test_python_version():
    assert sys.version_info.major == 3
    assert sys.version_info.minor >= 7


def test_data_dir(data_dir):
    # if this does not pass either data_dir was passed incorrectly or
    # pytest was not run from the download_scripts directory
    assert data_dir.is_dir()


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


def test_sum_stats_for_dups():
    data = {'pkey1': [1, 2, 3, 3, 4, 5, 5, 5],
            'pkey2': [2, 3, 4, 4, 5, 6, 6, 6],
            'stat1': [1, 2, 3, 4, 5, 6, 7, 8],
            'stat2': [1, 1, 1, 1, 1, 1, 1, 1],
            'misc': ['a', 'b', 'c1', 'c2', 'd', 'e1', 'e2', 'e3']}
    df = pd.DataFrame(data)

    df = dh.sum_stats_for_dups(df, ['pkey1', 'pkey2'], ['stat1', 'stat2'])

    chk = {'pkey1': [1, 2, 3, 4, 5],
           'pkey2': [2, 3, 4, 5, 6],
           'stat1': [1, 2, 7, 5, 21],
           'stat2': [1, 1, 2, 1, 3],
           'misc': ['a', 'b', 'c1', 'd', 'e1']}
    df_chk = pd.DataFrame(chk)

    assert df.equals(df_chk)
