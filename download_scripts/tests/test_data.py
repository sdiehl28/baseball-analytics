import pytest
import zipfile

__author__ = 'Stephen Diehl'

import pandas as pd
import numpy as np
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


def test_team_game_opponent_id_values(team_game):
    filt = team_game['at_home'] == False
    team_game['home_team_id'] = team_game['team_id']
    team_game.loc[filt, 'home_team_id'] = team_game.loc[filt, 'opponent_team_id']

    assert (team_game['game_id'].str[:3] == team_game['home_team_id']).all()


def test_batting_flags(batting):
    flag_cols = [
        'g',
        'g_dh',
        'g_ph',
        'g_pr'
    ]

    assert batting[flag_cols].min().min() == 0
    assert batting[flag_cols].max().max() == 1


def test_pitching_flags(pitching):
    flag_cols = [
        'g',
        'gs',
        'cg',
        'sho',
        'gf',
        'w',
        'l',
        'sv'
    ]

    assert pitching[flag_cols].min().min() == 0
    assert pitching[flag_cols].max().max() == 1


def test_fielding_flags(fielding):
    flag_cols = [
        'g',
        'gs'
    ]

    assert fielding[flag_cols].min().min() == 0
    assert fielding[flag_cols].max().max() == 1


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


def test_lahman_retro_batting_data(data_dir, batting):
    """Compare Aggregated Lahman batting data to Aggregated Retrosheet batting data

    The scripts must have worked correctly if the 17 batting fields
    in common have almost exactly the same sum between 1974 and 2019
    """
    filename = data_dir / 'lahman' / 'wrangled' / 'batting.csv'
    lahman_batting = dh.from_csv_with_types(filename)

    # Retrosheet data has no missing games since 1974
    filt = (batting['game_id'].str[3:7] >= '1974') & (batting['game_id'].str[3:7] <= '2019')
    r_batting = batting.loc[filt]

    # this could differ from 1974 and 2019 if not all those years were downloaded
    retro_min_year = r_batting['game_id'].str[3:7].astype('int').min()
    retro_max_year = r_batting['game_id'].str[3:7].astype('int').max()

    filt = (lahman_batting['year_id'] >= retro_min_year) & \
           (lahman_batting['year_id'] <= retro_max_year)
    l_batting = lahman_batting[filt]

    # columns in common -- these are the columns to compare
    b_cols = set(batting.columns) & set(lahman_batting.columns)
    b_cols -= {'player_id', 'team_id'}

    # there are 17 columns in common
    assert len(b_cols) == 17

    l_batting = l_batting[b_cols]
    r_batting = r_batting[b_cols]

    l_sums = l_batting.agg('sum').astype(int)
    l_sums.sort_index(inplace=True)

    r_sums = r_batting.agg('sum').astype(int)
    r_sums.sort_index(inplace=True)

    # verify all 17 batting attributes from 1974-2019
    # are within plus/minus 0.01% of each other when summed
    assert (np.abs(1.0 - (l_sums / r_sums)) < .0001).all()


def test_lahman_retro_pitching_data(data_dir, pitching):
    """Compare Aggregated Lahman pitching data to Aggregated Retrosheet pitching data

    The scripts must have worked correctly if the 19 pitching fields
    in common have almost exactly the same sum between 1974 and 2019
    """
    filename = data_dir / 'lahman' / 'wrangled' / 'pitching.csv'
    lahman_pitching = dh.from_csv_with_types(filename)

    # Retrosheet data has no missing games since 1974
    filt = (pitching['game_id'].str[3:7] >= '1974') & (pitching['game_id'].str[3:7] <= '2019')
    r_pitching = pitching.loc[filt]

    # this could differ from 1974 and 2019 if not all those years were downloaded
    retro_min_year = r_pitching['game_id'].str[3:7].astype('int').min()
    retro_max_year = r_pitching['game_id'].str[3:7].astype('int').max()

    filt = (lahman_pitching['year_id'] >= retro_min_year) & \
           (lahman_pitching['year_id'] <= retro_max_year)
    l_pitching = lahman_pitching[filt]

    # columns in common -- these are the columns to compare
    p_cols = set(l_pitching.columns) & set(r_pitching.columns)
    p_cols -= {'player_id', 'team_id'}

    # there are 21 columns in common
    assert len(p_cols) == 21

    l_pitching = l_pitching[p_cols]
    r_pitching = r_pitching[p_cols]

    l_sums = l_pitching.agg('sum').astype(int)
    l_sums.sort_index(inplace=True)

    r_sums = r_pitching.agg('sum').astype(int)
    r_sums.sort_index(inplace=True)

    # verify all values between 1974 and 2019 are within plus/minus 0.06% of each other
    assert (np.abs(1.0 - (l_sums / r_sums)) < .0006).all()


def test_lahman_retro_fielding_data(data_dir, fielding):
    """Compare Aggregated Lahman fielding per position data to
    Aggregated Retrosheet fielding per position data

    The scripts must have worked correctly if the 7 fielding fields
    in common have almost exactly the same sum between 1974 and 2019
    for every position.
    """
    filename = data_dir / 'lahman' / 'wrangled' / 'fielding.csv'
    lahman_fielding = dh.from_csv_with_types(filename)

    # Retrosheet data has no missing games since 1974
    filt = (fielding['game_id'].str[3:7] >= '1974') & (fielding['game_id'].str[3:7] <= '2019')
    r_fielding = fielding.loc[filt]
    r_fielding = r_fielding.rename(columns={'out': 'inn_outs'})

    # this could differ from 1974 and 2019 if not all those years were downloaded
    retro_min_year = r_fielding['game_id'].str[3:7].astype('int').min()
    retro_max_year = r_fielding['game_id'].str[3:7].astype('int').max()

    filt = (lahman_fielding['year_id'] >= retro_min_year) & \
           (lahman_fielding['year_id'] <= retro_max_year)
    l_fielding = lahman_fielding[filt]

    # find the common columns
    f_cols = (set(l_fielding.columns) & set(r_fielding.columns)) - {'player_id', 'pos', 'team_id'}
    f_cols = list(f_cols)

    l_sums = l_fielding.groupby('pos')[f_cols].aggregate('sum')
    l_sums.sort_index(inplace=True)

    # there are 7 fielding attributes and 7 fielding positions in Lahman
    assert l_sums.shape == (7, 7)

    r_sums = r_fielding.groupby('pos')[f_cols].aggregate('sum').astype('int')

    # Lahman uses OF for sum of LF, CF, RF
    r_sums.loc['OF'] = r_sums.loc['LF'] + r_sums.loc['CF'] + r_sums.loc['RF']
    r_sums = r_sums.drop(['LF', 'CF', 'RF'])
    r_sums.sort_index(inplace=True)

    # there are 7 fielding attributes and 7 fielding positions in Retrosheet
    assert r_sums.shape == (7, 7)

    # the indexes and columns should now be the same
    assert l_sums.index.equals(r_sums.index)
    assert l_sums.columns.equals(r_sums.columns)

    filt = r_fielding['pos'].isin(['LF', 'CF', 'RF'])
    r_of = r_fielding[filt]

    # account for outfielders who played more than 1 outfield position in the same game
    total_dups = r_of.duplicated(subset=['player_id', 'game_id'], keep=False).sum()
    counted_dups = r_of.duplicated(subset=['player_id', 'game_id'], keep='first').sum()
    r_sums.loc['OF', 'g'] -= (total_dups - counted_dups)

    rel_accuarcy = l_sums / r_sums

    # relative accuracy is within 0.8% for all 49 aggregated values
    assert (np.abs(1.0 - rel_accuarcy) < 0.008).all().all()


def test_batting_team_game_data(batting, team_game):
    """Verify Retrosheet batting aggregated by (game_id, team_id)
    is the same a team_game by (game_id, team_id)

    This shows that the two Retrosheet parsers are consistent with one another."""
    # team_game batting columns
    pkey = ['game_id', 'team_id']

    # batting columns to compare
    compare_cols = set(batting.columns) & set(team_game.columns) - set(pkey)
    compare_cols = list(compare_cols)

    assert len(compare_cols) == 17

    # sum all batting columns by the pkey of team_game, sort and reindex
    a = batting.groupby(['game_id', 'team_id'], as_index=False)[compare_cols].sum()
    a = a.sort_values(['game_id', 'team_id']).reset_index(drop=True)
    b = team_game[pkey + compare_cols].sort_values(['game_id', 'team_id']).reset_index(drop=True)

    assert a.equals(b)


def test_pitching_team_game_data(batting, pitching, team_game):
    """Verify Retrosheet batting aggregated by (game_id, team_id)
    is the same as team_game Pitching by (game_id, opponent_team_id)

    This shows that the two Retrosheet parsers are consistent with one another."""
    # team_game batting columns
    pkey = ['game_id', 'team_id']

    # columns to compare
    compare_cols = set(pitching.columns) & set(batting.columns) & set(team_game.columns) - set(pkey)
    compare_cols = list(compare_cols)

    assert len(compare_cols) == 14

    a = pitching.groupby(['game_id', 'team_id'], as_index=False)[compare_cols].sum()
    a = a.sort_values(['game_id', 'team_id']).reset_index(drop=True)

    b = team_game[['game_id', 'opponent_team_id'] + compare_cols].sort_values(
        ['game_id', 'opponent_team_id']).reset_index(drop=True)

    assert a[compare_cols].equals(b[compare_cols])


def test_fielding_team_game_data(fielding, team_game):
    """Verify Retrosheet fielding aggregated by (game_id, team_id)
    is the same a team_game by (game_id, team_id)

    This shows that the two Retrosheet parsers are consistent with one another."""
    pkey = ['game_id', 'team_id']

    # columns to compare
    compare_cols = set(fielding.columns) & set(team_game.columns) - set(pkey)

    # in fielding dp and tp are for those players involved, so this over counts
    # the total dp and tp in a game
    # there are more types of xi than just those by defensive players
    compare_cols -= {'dp', 'tp', 'xi'}
    compare_cols = list(compare_cols)

    assert len(compare_cols) == 4

    a = fielding.groupby(['game_id', 'team_id'], as_index=False)[compare_cols].sum()
    a = a.sort_values(['game_id', 'team_id']).reset_index(drop=True)
    b = team_game[pkey + compare_cols].sort_values(['game_id', 'team_id']).reset_index(drop=True)

    assert a.equals(b)


def test_batting_lahman_game_data(data_dir, batting):
    """Verify Retrosheet batting aggregated by (year_id, team_id_lahman)
    is the same as lahman_teams

    This shows that Retrosheet batting and Lahman Teams are consistent with each other."""

    filename = data_dir / 'lahman' / 'wrangled' / 'teams.csv'
    lahman_teams = dh.from_csv_with_types(filename)

    # Add year and only select between 1974 and 2019
    retro_batting = batting.copy()
    retro_batting['year_id'] = retro_batting['game_id'].str[3:7].astype('int')
    year_filt = (retro_batting['year_id'] >= 1974) & (retro_batting['year_id'] <= 2019)
    retro_batting = retro_batting[year_filt].copy()

    # Add team_id_lahman
    retro_batting = pd.merge(retro_batting, lahman_teams[['team_id', 'year_id', 'team_id_retro']],
                             left_on=['year_id', 'team_id'],
                             right_on=['year_id', 'team_id_retro'],
                             how='inner', suffixes=['_retrosheet', '_lahman'])

    # team_id_retro is now the same as team_id_retrosheet
    retro_batting.drop('team_id_retro', axis=1, inplace=True)

    pkey = ['year_id', 'team_id']
    compare_cols = set(lahman_teams.columns) & set(retro_batting.columns) - set(pkey)
    compare_cols -= {'g'}  # cannot sum g by player per team to get g per team
    compare_cols -= {'sb', 'cs'}  # these stats are close, but don't tie out as well as others
    compare_cols = list(compare_cols)

    assert len(compare_cols) == 10

    retro_batting_sums = retro_batting.groupby(['year_id', 'team_id_lahman'])[compare_cols].sum().astype('int')
    retro_batting_sums.sort_index(inplace=True)

    year_min, year_max = retro_batting['year_id'].aggregate(['min', 'max'])
    year_filt = (lahman_teams['year_id'] >= year_min) & (lahman_teams['year_id'] <= year_max)
    l_teams = lahman_teams.loc[year_filt, pkey + compare_cols]
    l_teams = l_teams.set_index(pkey).sort_index()

    # verify all 12880 values are within 0.5% of each other
    assert np.abs(1.0 - (l_teams / retro_batting_sums)).max().max() < 0.005


def test_attendance_values(game):
    # There was one baseball game in which the public was not allowed to attend.
    # This is considered null rather than 0, as people wanted to attend, but were not allowed.
    # https://www.baseball-reference.com/boxes/BAL/BAL201504290.shtml
    assert game['attendance'].min() > 0


def test_temperature_values(game):
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-temperature
    assert game['temperature'].min() > 0


def test_wind_speed_values(game):
    assert game['wind_speed'].min() >= 0


def test_wind_direction_values(game):
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-winddirection
    valid_values = ['to_lf', 'to_cf', 'to_rf', 'l_to_r', 'from_lf', 'from_cf',
                    'from_rf', 'r_to_l']
    assert game['wind_direction'].dropna().isin(valid_values).all()


def test_field_condition_values(game):
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-fieldcondition
    valid_values = ['soaked', 'wet', 'damp', 'dry']
    assert game['field_condition'].dropna().isin(valid_values).all()


def test_precip_type_values(game):
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-precipitation
    valid_values = ['none', 'drizzle', 'showers', 'rain', 'snow']
    assert game['precip_type'].dropna().isin(valid_values).all()


def test_sky_condition_values(game):
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-sky
    valid_values = ['sunny', 'cloudy', 'overcast', 'night', 'dome']
    assert game['sky_condition'].dropna().isin(valid_values).all()
