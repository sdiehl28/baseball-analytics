# Baseball Analytics
&#x1F534; Under Construction - may be ready for use by 12/31/19  

Scripts are provided to:

- download
- parse
- tidy
- validate and clean

Major League Baseball (MLB) data in preparation for easy analysis with Pandas or SQL.

The end result will be a set of csv files, with data types per column in associated csv files, which can be loaded into Pandas or any database.

Examples of baseball data analysis will be provided later in the form of Jupyter Notebooks.

## MLB Data Overview

### Lahman Overview

Lahman has MLB statistics summarized **per player per year** and **per team per year**.

The Lahman data is tidy and has several csv files.  The latest description of each csv file has been copied from the Lahman website to the `data/lahman` directory and is called readme2017.txt.  Loosely speaking, a description of data might be called "readme" or "data dictionary" or "code book".

As of December 2019, Lahman has data through the end of the 2019 season.  

Data is tidy if:

1. Each variable forms a column.
2. Each observation forms a row.
3. Each type of observational unit forms a table (or csv file).

### Retrosheet Overview

Retrosheet has play-by-play data for every MLB game since 1974.  Data is available since 1918 with older years having somewhat more missing data.  Open source parsers from Dr. T. L. Turocy will be used to parse and summarize the play-by-play data.

The **cwdaily** parser will generate a csv file with records **per player per game**.  This is a very large file as it includes all attributes for all roles a player may have (batter, pitcher, all 9 fielding positions) for all games.  Almost all the attributes are zero, as no player takes on all roles in a single game.  This output will be restructured into batting, pitching and fielding csv files with all records having at least 1 non-zero attribute.  This structure is almost identical to that used by Lahman.

The **cwgame** parser will generate a csv file that contains statistics for both teams per game and as well as game specific information such as attendance.  This output will be restructured into attributes **per team per game** and **per game**.

The description of the column headings for the parser generated csv files has been created and copied to `data/retrosheet` as cwdaily_datadictionary.txt and cwgame_datadictionary.txt.

As of December 2019, Retrosheet has data through the 2019 season.

### Field Names

The field names in both datasets are based on standard baseball statistic abbreviations.  See for example: https://en.wikipedia.org/wiki/Baseball_statistics or http://m.mlb.com/glossary/standard-stats

The field names have been changed as little as possible to remain familiar and yet meet Pandas and SQL naming conventions.

The field names in Lahman are changed from CamelCase to snake_case.  The field names created by the Retrosheet parsers are changed from upper case to lower case.  Invalid identifiers, such as 2B and 3B are changed to b_2B and b_3B (for batter hitting a double or triple).

Lahman and Retrosheet respectively use:

* gidp and gdp: for ground into double play
* hbp and hp: for hit by pitch

The Retrosheet field names will be changed to match the Lahman field names (gidp and hbp).

### Data Wrangling

Custom parsing of dates and times will be performed.  Data will be restructured.  Values that represent null will be converted to Pandas null (np.nan).  And more.

Data will be cleaned so that "primary keys" are unique.  Extremely few records require modification, but as most data processing relies on having a set of fields which uniquely identify a record, this cleaning is required.

Pandas datatypes will be optimized to save space and more accurately describe the attribute.  For example, the number of hits in a game is always between 0 and 255, so a uint8 can be used rather than an int64.  Likewise, for integer fields with missing values, the new Pandas Int64 (and similar) can be used instead of requiring a float datatype.

Datatype optimizations per column are persisted to disk for each corresponding csv file with the suffix `_types.csv`.  The Python functions **from_csv_with_types()** and **to_csv_with_types()** have been written to  allow persistence of data to/from csv files without losing data type information.

### Data Validation

pytest will be used to automate the running of data integrity tests, such as validating that the unique identifying fields are in fact, unique.

pytest:

* recommend: 'pytest -v --runslow'
* must be run from the `download_scripts` directory
* must be run after the scripts which download and parse the data have been run
* accepts custom option: --data-dir=<data_directory>
* accepts custom option: --runslow  # to run tests that depend on a slow to instantiate session fixture

### Data Consistency

To verify that the scripts worked correctly, the Retrosheet player per game and team per game data will be summarized to the yearly level and compared with Lahman.  This verification will be part of the supplied pytest tests.

### Statistics per Player Role

A baseball player may have several roles during the course of a game, such as batter, fielder, and pitcher.  Most attributes are unique to the role, but some are not.  The same player can hit a home run as a batter and allow a home run as a pitcher.

There are nine fielding roles.  For example, the same player could make a put-out while playing second base and later make a put-out while playing first base.

## Script Summary

Scripts are run from the download_scripts directory.  For more detail, see the README.md in the github download_scripts directory: [download_scripts](https://github.com/sdiehl28/baseball-analytics/tree/master/download_scripts)

Options include:

* -v for verbose which logs to stdout
* --log=INFO which logs (at the INFO level) to download.log
* --data-dir=../data which specifies the data directory (default is ../data)

Scripts with example command line arguments:

* **run_all_scripts.py** --data-dir=../data
  * convenience script to run all scripts
* **lahman_download.py** -v --log=INFO --data-dir=../data
  * downloads all the lahman data and unzips it to `../data/lahman/raw`

* **lahman_wrangle.py** -v -log=INFO --data-dir=../data
  * wrangles the Lahman data and persists it with optimized data types to `../data/lahman/wrange`
* **retrosheet_download.py** -v -log=INFO --data-dir=../data
  * downloads the Retrosheet data and unzips it to `../data/retrosheet/raw`
* **retrosheet_parse.py** -v --log=INFO --data-type --data-dir=../data
  * parses the play-by-play data using the cwdaily and cwgame open-source parsers
    * see [Parsers for Retrosheet](#Parsers-for-Retrosheet) below
    * all data in the `data/retrosheet/raw` is parsed with the results placed in `data/retrosheet/parsed`
  * all parsed data is collected into a one DataFrame for cwdaily and one DataFrame for cwgame and placed in `data/retrosheet/collected`
* **retrosheet_wrangle.py** -v --log=INFO --data-type --data-dir=../data
  *  wrangles the Retrosheet data and persists it with optimized data types to `../data/retrosheet/wrange`
* **pytest -v --runslow**
  * will kick off the functional and data integrity tests using tests/test_func.py and tests/test_data.py

## MLB Data Details

### Lahman

The most recent data will be downloaded from:  https://github.com/chadwickbureau/baseballdatabank/archive/master.zip

As per https://github.com/chadwickbureau/baseballdatabank readme.txt, regarding the **Lahman data license**:

```
This work is licensed under a Creative Commons Attribution-ShareAlike
3.0 Unported License.  For details see:
http://creativecommons.org/licenses/by-sa/3.0/
```

#### Lahman Data Dictionary

The most recent data dictionary is:  http://www.seanlahman.com/files/database/readme2017.txt  

This file is also copied to this repo at: `data/lahman/readme2017.txt`

#### Lahman CSV Data Files

The csv files for Lahman are tidy.  The lahman_download script will put these in: `../data/lahman/raw`

* **per player per year**
  * Batting.csv
  * Fielding.csv
  * Pitching.csv
* **per team per year**
  * Teams.csv
* **reference tables**
  * People.csv
  * Parks.csv
  * Salaries.csv
  * and more ...

### Retrosheet

The play-by-play data will be downloaded from: http://www.retrosheet.org/events/{year}eve.zip

The retrosheet_download script will put these in: `../data/retrosheet/raw`

As per: https://www.retrosheet.org/notice.txt regarding the **Retrosheet data license**:

```
     The information used here was obtained free of
     charge from and is copyrighted by Retrosheet.  Interested
     parties may contact Retrosheet at "www.retrosheet.org".
```

#### Generated CSV Data Files

The csv files must be generated by parsing the play-by-play data files.  The scripts will put the parsed csv files in:  `../data/retrosheet/parsed`.

The **cwdaily** parser generates statistics per player per game.  Attributes are prefixed by b for batter, p for pitcher and f_{pos} for fielder where pos is one of P, C, 1B, 2B, 3B, SS, LF, CF, RF.

The **cwgame** parser generates statistics per game for both teams.

#### Retrosheet Data Dictionary

The retrosheet_datadictionary.py script will generate a description of the output of the cwdaily and cwgame parsers.

This script has been run and the descriptions have been saved to:  `data/retrosheet/cwdaily_datadictionary.txt` and `data/retrosheet/cwgame_datadictionary.txt`

## Parsers for Retrosheet

The open source parsers created by Dr. T. L. Turocy will be used.

As per https://github.com/chadwickbureau/chadwick README, regarding the parser license:

```
This is Chadwick, a library and toolset for baseball play-by-play
and statistics.

Chadwick is Open Source software, distributed under the terms of the 
GNU General Public License (GPL).
```

Parser Description: http://chadwick.sourceforge.net/doc/cwtools.html  
Parser Executables and Source: https://sourceforge.net/projects/chadwick/  

At the time of this writing, version 0.7.2 is the latest version.  Executable versions of the parsers are available for Windows.  Source code is available for Linux and MacOS.

### How to Build Retrosheet Parsers on Linux

If you do not already have a build environment:

1. sudo apt install gcc
2. sudo apt install build-essential

cd to the source directory:

1. ./configure
2. make
3. sudo make install

Result

1. The cw command line tools will be installed in /usr/local/bin.
2. The cw library will be installed in /usr/local/lib.

To allow the command line tools to find the shared libraries, add the following to your .bashrc and then: source .bashrc
`export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib`