"""Baseball Data Helper Functions"""

__author__ = 'Stephen Diehl'

import pandas as pd
import numpy as np
import re
import io
from pathlib import Path
import statsmodels.api as sm
from IPython.display import HTML, display
from sqlalchemy.types import SmallInteger, Integer, BigInteger, Float


def to_csv_with_types(df, filename):
    """
    Save df to csv file and save df.dtypes to csv file.

    If filename ends in .gz, Pandas will use gzip compression.

    This is intended to be used after optimizing df column types.
    Read back with: from_csv_with_types()

    Persistence with data types cannot currently be done with hdf5 because
    the new Int64 and similar data types are not supported.
    """

    p = Path(filename)
    types_name = p.name.split('.')[0] + '_types.csv'
    p_types = p.parent / types_name

    dtypes = df.dtypes.to_frame('dtypes').reset_index()

    dtypes.to_csv(p_types, index=False)
    df.to_csv(p, index=False)


def from_csv_with_types(filename, usecols=None, nrows=None):
    """
    Read df.dtypes from csv file and read df from csv file.

    If filename ends in .gz, Pandas will use gzip decompression.
    This is the complement of to_csv_with_types().
    """

    p = Path(filename)
    types_name = p.name.split('.')[0] + '_types.csv'
    p_types = p.parent / types_name
    dates, dtypes = read_types(p_types)

    # only parse dates that are in usecols
    if dates and usecols:
        dates = list(set(dates) & set(usecols))

    return pd.read_csv(p, parse_dates=dates, dtype=dtypes, usecols=usecols, nrows=nrows)


def read_types(filename):
    """Read data types file to get list of date fields and a dictionary mapping of types

    """
    types = pd.read_csv(filename).set_index('index').to_dict()
    dtypes = types['dtypes']

    dates = [key for key, value in dtypes.items() if value.startswith('datetime')]
    for field in dates:
        dtypes.pop(field)

    return dates, dtypes


def get_optimal_data_type(s):
    # if the integer is outside the range of values that be converted to a nullable integer type
    # use float64
    convert_type = 'float64'

    dtype_range = get_dtype_range()
    if s.min() >= 0:
        for dtype in ['UInt8', 'UInt16', 'UInt32', 'UInt64']:
            if s.max() <= dtype_range[dtype][2]:
                convert_type = dtype
                break
    else:
        for dtype in ['Int8', 'Int16', 'Int32', 'Int64']:
            if s.max() <= dtype_range[dtype][2] and s.min() >= dtype_range[dtype][1]:
                convert_type = dtype
                break

    return convert_type


def optimize_df_dtypes(df, ignore=None):
    """
    Downcasts DataFrame Column Types based on values.

    Modification is inplace.

    Parameters:
        df (pd.DataFrame): reduce size of datatypes as appropriate for its values.

       ignore (list): column names to exclude from downcasting.
    """

    # columns to consider for downcasting
    process_cols = df.columns
    if ignore:
        process_cols = df.columns.difference(ignore)

        if len(process_cols) == 0:
            return df

    # get the integer columns, if any
    df_int = df[process_cols].select_dtypes(include=[np.int])

    # downcast integer columns to smallest unsigned int that will hold the values
    if len(df_int.columns) > 0:
        df[df_int.columns] = df_int.apply(pd.to_numeric, downcast='unsigned')

    # if there were any negative values, the above creates int64, downcast int64 as well
    df_int64 = df[process_cols].select_dtypes(include=[np.int64])
    if len(df_int64.columns) > 0:
        df[df_int64.columns] = df_int64.apply(pd.to_numeric, downcast='signed')

    # convert float columns that are integers with nans to best nullable integer type
    df_float = df.select_dtypes(include=['float'])
    if len(df_float.columns) > 0:
        filt = df_float.apply(is_int)
        int_col_names = df_float.columns[filt]
        if filt.any():
            for col in int_col_names:
                convert_type = get_optimal_data_type(df[col])
                df[col] = df[col].astype(convert_type)


def get_dtype_range():
    """Create a Dictionary having min/max values per Data Type

    Key: string representation of data type
    Value: list of length 3
      value[0] is 0 or np.nan
      value[1] is min for that data type
      value[2] is max for that data type

    This dictionary can be used to create a 3 row DataFrame which demonstrates
    that the specified data type can hold the specified values.

    Pandas data type limits:
    Int8   nullable with same limits as np.int8
    UInt8  nullable with same limits as np.uint8
    Int16  nullable with same limits as np.int16
    UInt16 nullable with same limits as np.uint16
    Int32  nullable with same limits as np.int32
    UInt32 nullable with same limits as np.uint32
    Int64  nullable with min/max limits about 1/2 of np.int64
    UInt64 nullable with max limit about 1/4 of np.uint64
    """
    data = []
    for dtype in ['uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64', 'int64']:
        data.append([0, np.iinfo(dtype).min, np.iinfo(dtype).max])
        data.append([np.nan, np.iinfo(dtype).min, np.iinfo(dtype).max])

    keys = ['uint8', 'UInt8', 'int8', 'Int8', 'uint16', 'UInt16', 'int16', 'Int16',
            'uint32', 'UInt32', 'int32', 'Int32', 'uint64', 'UInt64', 'int64', 'Int64']

    dtype_range = dict(zip(keys, data))

    # Pandas has different limits than numpy for the following
    dtype_range['UInt64'][2] = 2**61
    dtype_range['Int64'][1] = -2**61
    dtype_range['Int64'][2] = 2**61

    return dict(zip(keys, data))


def optimize_db_dtypes(df):
    """
    Choose smallest ANSI SQL Column Type for integer that fits the optimized DataFrame.

    Relies on:
    from sqlalchemy.types import SmallInteger, Integer, BigInteger

    SQL Column Types are signed, so uint16 might not fit in smallinteger
    TODO: below is safe but inefficient for uint16, UInt16, uint32 and UInt32
    """
    small_int = {col: SmallInteger for col in df.select_dtypes(
        include=[pd.Int8Dtype, np.int8, pd.UInt8Dtype, np.uint8,
                 pd.Int16Dtype, np.int16]).columns}

    integer = {col: Integer for col in df.select_dtypes(
        include=[pd.UInt16Dtype, np.uint16, pd.Int32Dtype, np.int32]).columns}

    big_int = {col: BigInteger for col in df.select_dtypes(
        include=[pd.UInt32Dtype, np.uint32, pd.Int64Dtype, np.int64]).columns}

    # use double precision for unsigned 64 bit integers
    # Float(precision=53) is the SQL data type for double precision
    double = {col: Float(precision=53) for col in df.select_dtypes(
        include=[np.uint64, pd.UInt64Dtype]).columns}

    dtypes = {**small_int, **integer, **big_int, **double}

    return dtypes


def mem_usage(df):
    """Returns a string representing df memory usage in MB."""
    mem = df.memory_usage(deep=True).sum()
    mem = mem / 2 ** 20  # covert to megabytes
    return f'{mem:03.2f} MB'


def is_int(s):
    """Returns True if all non-null values are integers.

    Useful for determining if the df column (pd.Series) is
    float just to hold missing values.
    """
    notnull = s.notnull()
    is_integer = s.apply(lambda x: (x % 1 == 0.0))
    return (notnull == is_integer).all()


def convert_camel_case(name):
    """
    CamelCase to snake_case.

    This is from:
    https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case#answer-1176023
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def is_unique(df, cols, ignore_null=False):
    """Fast determination of multi-column uniqueness."""
    if ignore_null:
        df.dropna(subset=cols, inplace=True)
    return not (df.duplicated(subset=cols)).any()


def df_info(df):
    """Use buffer to capture output from df.info()"""
    buffer = io.StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()


def order_cols(df, cols):
    """Put columns in cols first, followed by rest of columns"""
    rest = [col for col in df.columns if col not in cols]
    df = df[cols + rest]
    return df


def sum_stats_for_dups(df, pkey, stat_cols):
    """Sum stat columns for rows having the same primary key.

    This is a "best guess" fix to rows with duplicate primary keys.

    The first value for a non-pkey non-stat column will be kept.
    """
    # dups is true for all rows that are duplicates
    dups = df.duplicated(subset=pkey, keep=False)
    if len(dups) == 0:
        return

    # get the duplicated rows
    df_dups = df.loc[dups]

    # for the duplicate rows, sum the stat columns only
    df_summed = df_dups.groupby(pkey)[stat_cols].sum()

    # often, setting the index to the primary key makes data processing easier
    df.set_index(pkey, inplace=True)

    # remove all but one of each group of duplicated rows
    df = df.loc[~df.index.duplicated(keep='first')].copy()

    # set the kept row (per group) equal to the summed row computed above
    df.loc[df_summed.index, stat_cols] = df_summed

    df.reset_index(inplace=True)

    return df


def move_column_after(df, after_col, col):
    idx = df.columns.get_loc(after_col)
    cols = list(df.columns)
    cols.remove(col)
    cols.insert(idx + 1, col)
    return df.reindex(cols, axis=1)


def game_id_to_url(game_id):
    """Game ID to URL for Jupyter Notebooks"""
    dir = game_id[:3]
    url = 'https://www.baseball-reference.com/boxes/' + dir + '/' + game_id + '.shtml'
    display(HTML(f'<a href="{url}">{game_id}</a>'))


def player_id_to_url(player_id):
    """Baseball Reference Player ID to URL for Jupyter Notebooks"""
    dir = player_id[0]
    url = 'https://www.baseball-reference.com/players/' + dir + '/' + player_id + '.shtml'
    display(HTML(f'<a href="{url}">{player_id}</a>'))


def simple_loess(x, y, df, frac=1 / 6, it=0):
    """Smoothes noisy data.

    Increase frac to get more smoothing.
    Decrease frac to get less smoothing.

    sns.lmplot has a loess option, but it uses poor and unchangeable defaults."""
    z = sm.nonparametric.lowess(df[y], df[x], frac=frac, it=it)
    return pd.DataFrame(data=z, columns=[x, y])
