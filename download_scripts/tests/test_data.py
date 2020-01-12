import pytest
import zipfile

__author__ = 'Stephen Diehl'

import pandas as pd
import numpy as np
from .. import data_helper as dh


def test_lahman_download(data_dir):
    """Verify the Lahman Data was downloaded, unzipped and reogranized."""
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
    """Verify the Retrosheet data was downloaded and and unzipped."""
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


def test_download_years(batting):
    """Verify the Retrosheet years 1974 through 2019 inclusive were downloaded.

    The data consistency tests have accuracy bounds tested on these years only!"""
    assert (batting['game_start_dt'].agg(['min', 'max']).dt.year == (1974, 2019)).all()
    assert batting['game_start_dt'].dt.year.nunique() == (2019 - 1974) + 1


def test_lahman_people_pkey(lahman_people):
    """Verify the Lahman People primary and foreign keys."""
    assert dh.is_unique(lahman_people, ['player_id'])  # lahman player id
    assert dh.is_unique(lahman_people, ['retro_id'], ignore_null=True)  # retrosheet player id


def test_lahman_fielding_pkey(lahman_fielding):
    """Verfiy the Lahman Fielding primary keys."""
    assert dh.is_unique(lahman_fielding, ['player_id', 'year', 'stint', 'pos'])


def test_lahman_batting_pkey(lahman_batting):
    """Verify the Lahman Batting primary key."""
    assert dh.is_unique(lahman_batting, ['player_id', 'year', 'stint'])


def test_lahman_pitching_pkey(lahman_pitching):
    """Verify the Lahman Pitching primary key."""
    assert dh.is_unique(lahman_pitching, ['player_id', 'year', 'stint'])


def test_lahman_salaries_pkey(data_dir):
    """Verify the Lahman Salaries primary key."""
    filename = data_dir / 'lahman' / 'wrangled' / 'salaries.csv'

    # check for duplicate IDs
    salaries = dh.from_csv_with_types(filename)
    assert dh.is_unique(salaries, ['player_id', 'year', 'team_id'])


def test_lahman_teams_pkey(lahman_teams):
    """Verify the Lahman Teams primary key."""
    assert dh.is_unique(lahman_teams, ['team_id', 'year'])  # lahman team_id
    assert dh.is_unique(lahman_teams, ['team_id_retro', 'year'])  # retrosheet team_id


def test_lahman_parks_pkey(data_dir):
    """Verify the Lahman Parks primary key."""
    filename = data_dir / 'lahman' / 'wrangled' / 'parks.csv'

    # check for duplicate IDs
    parks = dh.from_csv_with_types(filename)
    assert dh.is_unique(parks, ['park_key'])

    # park_name is not unique
    # assert dh.is_unique(parks, ['park_name']


def test_team_game_opponent_id_values(team_game):
    "Verify opponent_team_id in Retrosheet team_game"
    filt = team_game['at_home'] == False
    team_game['home_team_id'] = team_game['team_id']
    team_game.loc[filt, 'home_team_id'] = team_game.loc[filt, 'opponent_team_id']

    assert (team_game['game_id'].str[:3] == team_game['home_team_id']).all()


def test_batting_flags(batting):
    """Verify the batting flags are 0 or 1.

    g means in the game in the specified role.
    For example, g_pr means in the game as a pinch runner."""
    flag_cols = [
        'g',
        'g_dh',
        'g_ph',
        'g_pr'
    ]

    assert batting[flag_cols].min().min() == 0
    assert batting[flag_cols].max().max() == 1


def test_pitching_flags(pitching):
    """Verify the pitching flags are 0 or 1.

    For example:
    gs means the pitcher started the game
    gf means the pitcher finished the game"""
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
    """Verify the fielding flags are either 0 or 1."""
    flag_cols = [
        'g',
        'gs'
    ]

    assert fielding[flag_cols].min().min() == 0
    assert fielding[flag_cols].max().max() == 1


def test_batting_pkey(batting):
    """Verify the Retrosheet batting primary key."""
    assert dh.is_unique(batting, ['player_id', 'game_id'])


def test_pitching_pkey(pitching):
    """Verify the Retrosheet pitching primary key."""
    assert dh.is_unique(pitching, ['player_id', 'game_id'])


def test_fielding_pkey(fielding):
    """Verify the Retrosheet fielding primary key."""
    assert dh.is_unique(fielding, ['player_id', 'game_id', 'pos'])


def test_team_game_pkey(team_game):
    """Verify the Retrosheet team_game primary key."""
    assert dh.is_unique(team_game, ['team_id', 'game_id'])


def test_game_pkey(game):
    """Verify the Retrosheet game primary key."""
    assert dh.is_unique(game, ['game_id'])


def test_lahman_retro_batting_data(batting, lahman_batting):
    """Compare Aggregated Lahman batting data to Aggregated Retrosheet batting data"""
    # columns in common -- these are the columns to compare
    b_cols = set(batting.columns) & set(lahman_batting.columns)
    b_cols -= {'player_id', 'team_id'}

    # there are 17 columns in common
    assert len(b_cols) == 17

    l_batting = lahman_batting[b_cols]
    r_batting = batting[b_cols]

    l_sums = l_batting.agg('sum').astype(int)
    l_sums.sort_index(inplace=True)

    r_sums = r_batting.agg('sum').astype(int)
    r_sums.sort_index(inplace=True)

    # verify all 17 batting attributes
    # are within plus/minus 0.01% of each other when summed
    assert (np.abs(1.0 - (l_sums / r_sums)) < .0001).all()


def test_lahman_retro_pitching_data(pitching, lahman_pitching):
    """Compare Aggregated Lahman pitching data to Aggregated Retrosheet pitching data"""
    # columns in common -- these are the columns to compare
    p_cols = set(lahman_pitching.columns) & set(pitching.columns)
    p_cols -= {'player_id', 'team_id'}

    # there are 21 columns in common
    assert len(p_cols) == 21

    l_pitching = lahman_pitching[p_cols]
    r_pitching = pitching[p_cols]

    l_sums = l_pitching.agg('sum').astype(int)
    l_sums.sort_index(inplace=True)

    r_sums = r_pitching.agg('sum').astype(int)
    r_sums.sort_index(inplace=True)

    # verify all values are within plus/minus 0.06% of each other
    assert (np.abs(1.0 - (l_sums / r_sums)) < .0006).all()


def test_lahman_retro_fielding_data(fielding, lahman_fielding):
    """Compare Aggregated Lahman fielding per position data to
    Aggregated Retrosheet fielding per position data."""
    # find the common columns
    f_cols = (set(lahman_fielding.columns) & set(fielding.columns)) - {'player_id', 'pos', 'team_id'}
    f_cols = list(f_cols)

    l_sums = lahman_fielding.groupby('pos')[f_cols].aggregate('sum')
    l_sums.sort_index(inplace=True)

    # there are 7 fielding attributes and 7 fielding positions in Lahman
    assert l_sums.shape == (7, 7)

    r_sums = fielding.groupby('pos')[f_cols].aggregate('sum').astype('int')

    # Lahman uses OF for sum of LF, CF, RF
    r_sums.loc['OF'] = r_sums.loc['LF'] + r_sums.loc['CF'] + r_sums.loc['RF']
    r_sums = r_sums.drop(['LF', 'CF', 'RF'])
    r_sums.sort_index(inplace=True)

    # there are now 7 fielding attributes and 7 fielding positions in Retrosheet sums
    assert r_sums.shape == (7, 7)

    # the indexes and columns should now be the same
    assert l_sums.index.equals(r_sums.index)
    assert l_sums.columns.equals(r_sums.columns)

    filt = fielding['pos'].isin(['LF', 'CF', 'RF'])
    r_of = fielding[filt]

    # account for outfielders who played more than 1 outfield position in the same game
    total_dups = r_of.duplicated(subset=['player_id', 'game_id'], keep=False).sum()
    counted_dups = r_of.duplicated(subset=['player_id', 'game_id'], keep='first').sum()
    r_sums.loc['OF', 'g'] -= (total_dups - counted_dups)

    rel_accuarcy = l_sums / r_sums

    # relative accuracy is within 0.8% for all 49 aggregated values
    assert (np.abs(1.0 - rel_accuarcy) < 0.008).all().all()


def test_batting_team_game_data(batting, team_game):
    """Verify Retrosheet batting aggregated by (game_id, team_id)
    is the same as team_game batting stats."""
    exclude = ['game_id', 'team_id', 'player_id', 'game_start_dt']
    cols = set(batting.columns) & set(team_game.columns) - set(exclude)
    cols = list(cols)

    assert len(cols) == 17

    b = batting[['game_id', 'team_id'] + cols].groupby(['game_id', 'team_id']).agg('sum')
    b = b.reset_index().sort_index()

    tg = team_game[['game_id', 'team_id'] + cols].sort_values(
        ['game_id', 'team_id']).reset_index(drop=True)

    assert b.equals(tg)


def test_pitching_team_game_data(pitching, team_game):
    """Verify Retrosheet batting aggregated by (game_id, team_id)
    is the same as team_game pitching stats

    This shows that the two Retrosheet parsers are consistent with one another."""
    cols = ['wp', 'bk', 'er']

    p = pitching[['game_id', 'team_id'] + cols].groupby(['game_id', 'team_id']).agg('sum')
    p = p.reset_index().sort_index()

    tg = team_game[['game_id', 'team_id'] + cols].sort_values(
        ['game_id', 'team_id']).reset_index(drop=True)

    assert p.equals(tg)


def test_fielding_team_game_data(fielding, team_game):
    """Verify Retrosheet fielding aggregated by (game_id, team_id)
    is the same a team_game fielding stats

    This shows that the two Retrosheet parsers are consistent with one another."""
    cols = ['a', 'e', 'po', 'pb']

    f = fielding[['game_id', 'team_id'] + cols].groupby(['game_id', 'team_id']).agg('sum')
    f = f.reset_index().sort_index()

    tg = team_game[['game_id', 'team_id'] + cols].sort_values(
        ['game_id', 'team_id']).reset_index(drop=True)

    assert f.equals(tg)


def test_batting_lahman_game_data(batting, lahman_teams):
    """Verify Retrosheet batting aggregated by (year, team_id_lahman)
    is the same as Lahman_teams.

    This shows that Retrosheet batting and Lahman Teams are consistent with each other."""
    batting = batting.copy()
    batting['year'] = batting['game_start_dt'].dt.year

    # Add team_id_lahman
    retro_batting = pd.merge(batting, lahman_teams[['team_id', 'year', 'team_id_retro']],
                             left_on=['year', 'team_id'],
                             right_on=['year', 'team_id_retro'],
                             how='inner', suffixes=['_retrosheet', '_lahman'])

    # team_id_retro is now the same as team_id_retrosheet
    retro_batting.drop('team_id_retro', axis=1, inplace=True)

    pkey = ['year', 'team_id']
    compare_cols = set(lahman_teams.columns) & set(retro_batting.columns) - set(pkey)
    compare_cols -= {'g'}  # cannot sum g by player per team to get g per team
    compare_cols -= {'sb', 'cs'}  # these stats are close, but don't tie out as well as others
    compare_cols = list(compare_cols)

    assert len(compare_cols) == 10

    retro_batting_sums = retro_batting.groupby(['year', 'team_id_lahman'])[compare_cols].sum().astype('int')
    retro_batting_sums.sort_index(inplace=True)

    year_min, year_max = retro_batting['year'].aggregate(['min', 'max'])
    year_filt = (lahman_teams['year'] >= year_min) & (lahman_teams['year'] <= year_max)
    l_teams = lahman_teams.loc[year_filt, pkey + compare_cols]
    l_teams = l_teams.set_index(pkey).sort_index()

    # verify all 12880 values are within 0.5% of each other
    assert np.abs(1.0 - (l_teams / retro_batting_sums)).max().max() < 0.005


def test_attendance_values(game):
    """Verify attendance has plausible values."""
    # There was one baseball game in which the public was not allowed to attend.
    # This is considered null rather than 0, as people wanted to attend, but were not allowed.
    # https://www.baseball-reference.com/boxes/BAL/BAL201504290.shtml
    assert game['attendance'].min() > 0


def test_temperature_values(game):
    """Verify temperature has plausible values."""
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-temperature
    assert game['temperature'].min() > 0


def test_wind_speed_values(game):
    """Verify wind speed has plausible values."""
    assert game['wind_speed'].min() >= 0


def test_wind_direction_values(game):
    """Verfiy wind direction is in known category."""
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-winddirection
    valid_values = ['to_lf', 'to_cf', 'to_rf', 'l_to_r', 'from_lf', 'from_cf',
                    'from_rf', 'r_to_l']
    assert game['wind_direction'].dropna().isin(valid_values).all()


def test_field_condition_values(game):
    """Verify field condition is in known category."""
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-fieldcondition
    valid_values = ['soaked', 'wet', 'damp', 'dry']
    assert game['field_condition'].dropna().isin(valid_values).all()


def test_precip_type_values(game):
    """Verify precipition type is in known category."""
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-precipitation
    valid_values = ['none', 'drizzle', 'showers', 'rain', 'snow']
    assert game['precip_type'].dropna().isin(valid_values).all()


def test_sky_condition_values(game):
    """Verify sky condition is in known category."""
    # http://chadwick.sourceforge.net/doc/cwgame.html#cwtools-cwgame-sky
    valid_values = ['sunny', 'cloudy', 'overcast', 'night', 'dome']
    assert game['sky_condition'].dropna().isin(valid_values).all()


def test_game_length_values(game):
    """Verify number of outs is consistent with number of innings."""
    outs = game['game_length_outs']
    inns = game['game_length_innings']

    # this is defined by the rules of baseball
    assert ((5 * inns <= outs) & (outs <= 6 * inns)).all()


def test_game_length_minute_values(game):
    """Verify game length per out is plausible."""
    outs = game['game_length_outs']
    mins = game['game_length_minutes']
    mins_per_out = mins / outs

    # these bounds should be wide enough to encompass any future game
    assert ((mins_per_out.min() > 1) & (mins_per_out.max() < 6)).all()


def test_retro_lahman_batting_players(batting, lahman_people, lahman_batting):
    """Verify all Retrosheet batters are in Lahman batting"""
    lahman_batters = pd.merge(lahman_batting['player_id'], lahman_people[['player_id', 'retro_id']])
    r_batters = set(batting['player_id'].unique())
    l_batters = set(lahman_batters['retro_id'].unique())
    assert r_batters == l_batters


def test_retro_lahman_fielding_players(fielding, lahman_people, lahman_fielding):
    """Verify all Retrosheet fielders are in Lahman fielding"""
    lahman_fielders = pd.merge(lahman_fielding['player_id'], lahman_people[['player_id', 'retro_id']])
    r_fielders = set(fielding['player_id'].unique())
    l_fielders = set(lahman_fielders['retro_id'].unique())

    # There is one Retrosheet fielder not in Lahman fielding
    assert len(r_fielders - l_fielders) == 1
    assert len(l_fielders - r_fielders) == 0

    missing_fielder = f'{(r_fielders - l_fielders).pop()}'
    missing = fielding.query(f'player_id == "{missing_fielder}"')

    # The missing fielder had zero fielding total chances.
    assert missing['tc'].sum() == 0


def test_retro_lahman_pitching_players(pitching, lahman_pitching, lahman_people):
    """Verify all Retrosheet pitchers are in Lahman pitchers"""
    lahman_pitchers = pd.merge(lahman_pitching['player_id'], lahman_people[['player_id', 'retro_id']])
    r_pitchers = set(pitching['player_id'].unique())
    l_pitchers = set(lahman_pitchers['retro_id'].unique())
    assert r_pitchers == l_pitchers


def test_retro_lahman_player_ids(batting, lahman_people):
    """Verify the inverse of Lahman player_id to Retrosheet player_id mapping is valid.

    In other words, each Retrosheet player_id is mapped to exactly one Lahman player_id.

    In math terms, Lahman player_id to Retrosheet player_id is one-to-one and onto.

    Other tests verify that Retrosheet player_ids and Lahman player_ids are unique.

    Note: every player who was in a game, has a Retrosheet batting record even if
    they had no plate appearances."""
    retro_players = pd.Series(batting['player_id'].unique(), name='player_id')

    # use an inner join to verify that the mapping is one-to-one and onto
    mapping = lahman_people[['player_id', 'retro_id']].merge(
        retro_players, how='inner',
        left_on=['retro_id'],
        right_on=['player_id'],
        suffixes=('_lahman', '_retro'))

    assert len(retro_players) == len(mapping)


def test_retro_lahman_team_ids(team_game, lahman_teams):
    """Verify the inverse of the Lahman <team_id> to Retroshett <team_id> mapping is valid.
    A <team_id> is (team_id, year).

    The logic is analogous test_retro_lahman_player_ids() above."""

    # create a Retrosheet dataframe having just the unique <team_id> values
    retro_team_ids = team_game[['team_id', 'game_start_dt']].copy()
    retro_team_ids['year'] = retro_team_ids['game_start_dt'].dt.year
    retro_team_ids = retro_team_ids.drop_duplicates(subset=['team_id', 'year'])

    # use an inner join to verify that the mapping is one-to-one and onto
    mapping = lahman_teams.merge(retro_team_ids, how='inner',
                                 left_on=['team_id_retro', 'year'],
                                 right_on=['team_id', 'year'])

    assert len(retro_team_ids) == len(mapping)


def test_retro_pitching_batting(pitching, batting):
    """Verify Retrosheet batting stats == pitching stats (allowed)"""
    exclude = ['game_id', 'team_id', 'player_id', 'g', 'game_start_dt']
    cols = set(pitching.columns) & set(batting.columns) - set(exclude)
    cols = list(cols)
    assert len(cols) == 16

    # sum over all pitchers over all years
    p = pitching[cols].agg('sum')

    # sum over all batters over all years
    b = batting[cols].agg('sum')

    # Retrosheet is completely consistent
    p.equals(b)


def test_lahman_pitching_batting(lahman_pitching, lahman_batting):
    """Verify Lahman batting stats == pitching stats (allowed)"""
    exclude = ['lg_id', 'player_id', 'stint', 'team_id', 'year', 'g']
    cols = set(lahman_pitching.columns) & set(lahman_batting.columns)
    cols -= set(exclude)
    assert len(cols) == 10

    # sum over all pitchers over all years
    p = lahman_pitching[cols].agg('sum')

    # sum over all batters over all years
    b = lahman_batting[cols].agg('sum')

    # the biggest difference is less than 0.01%
    assert (np.abs(1.0 - p / b).max() < 0.0001).all()


def test_lahman_batting_teams(lahman_batting, lahman_teams):
    """Verify Lahman batting aggregated to the team level matches Lahman teams."""
    exclude = ['lg_id', 'team_id', 'year', 'g']
    key = ['team_id', 'year']
    cols = set(lahman_batting.columns) & set(lahman_teams.columns) - set(exclude)
    cols = list(cols)
    assert len(cols) == 12

    b = lahman_batting[key + cols].groupby(key).agg('sum').reset_index()

    t = lahman_teams[key + cols].sort_values(key).reset_index(drop=True)

    # ensure the dtypes are the same
    for col in t.columns:
        if not col == 'team_id' and not col == 'year':
            b[col] = b[col].astype('int')
            t[col] = t[col].astype('int')

    assert b[cols].equals(t[cols])


def test_lahman_pitching_teams(lahman_pitching, lahman_teams):
    """Verify Lahman pitching aggregated to the team level matches Lahman teams."""
    # most of the common columns are for batting, not pitching
    # era cannot be summed
    # sho for team is counted differently than for pitcher
    # er for team is counted differently than for pitcher
    exclude = ['lg_id', 'team_id', 'year', 'g', 'era',
               'bb', 'h', 'hbp', 'hr', 'r', 'sf', 'so', 'sho', 'er']
    key = ['team_id', 'year']
    cols = set(lahman_pitching.columns) & set(lahman_teams.columns) - set(exclude)
    cols = list(cols)
    assert len(cols) == 5

    p = lahman_pitching[key + cols].groupby(key).agg('sum').reset_index()

    t = lahman_teams[key + cols].sort_values(key).reset_index(drop=True)

    # dtypes need to be the same
    for col in p.columns:
        if not col == 'year' and not col == 'team_id':
            p[col] = p[col].astype('int')
            t[col] = t[col].astype('int')

    assert np.abs(p[col] - t[col]).max() == 1


def test_lahman_fielding_teams(lahman_fielding, lahman_teams):
    """Verify Lahman fielding aggregated to the team level matches Lahman teams."""
    # dp is excluded because in fielding, each fielder involved gets a dp
    # whereas in team only one dp is counted
    exclude = ['lg_id', 'team_id', 'year', 'g', 'dp', 'player_id']
    key = ['team_id', 'year']
    cols = set(lahman_fielding.columns) & set(lahman_teams.columns) - set(exclude)
    cols = list(cols)
    assert len(cols) == 1

    f = lahman_fielding[key + cols].groupby(key).agg('sum').reset_index()

    t = lahman_teams[key + cols].sort_values(key).reset_index(drop=True)

    # ensure the dtypes are the same
    col = 'e'
    f[cols] = f[cols].astype('int')
    t[cols] = t[cols].astype('int')

    # When comparing large values, it is best to use their relative differences.
    # When comparing small values, it is best to use their absolute differences.
    assert ((f[cols] - t[cols]).max() <= 2).all()
