# Baseball Analytics
&#x1F534; Under Construction - may be ready for use by 12/29/19  

Scripts are provided to:

- download
- parse
- tidy
- validate and clean

Major League Baseball (MLB) data in preparation for easy analysis with Pandas or SQL.

The end result will be a set of csv files, with data types per column in associated csv files, which can be loaded into Pandas or any database.

Examples of baseball data analysis will be provided later in the form of Jupyter Notebooks.

### MLB Data

Lahman has MLB statistics summarized by **player per year** and by **team per year**.

Retrosheet has play-by-play data for every MLB game since 1974.  Data is available since 1918 with older years having somewhat more missing data.  This data can be parsed to summarize statistics by **player per game** and **team per game**.

The Lahman data is tidy and has several csv files.  The latest available description of each csv file has been copied to the `data/lahman` directory.

Data is tidy if:

1. Each variable forms a column.
2. Each observation forms a row.
3. Each type of observational unit forms a table (or csv file).

The Retorsheet data is not distributed as csv files, but as text files which have play-by-play information.  This data will be parsed and aggregated to the game level, using open source parsers from Dr. T. L. Turocy as described below.  The description of the generated csv files can also be generated from the parsers.  These descriptions have been generated and copied to the `data/retrosheet` directory.

As of December 2019, Lahman has data through the 2018 season whereas Retrosheet has data through the 2019 season.

### Field Names

The field names in both datasets are based on standard baseball statistic abbreviations.  See for example: https://en.wikipedia.org/wiki/Baseball_statistics

The field names in Lahman will be changed from CamelCase to snake_case.  The field names in both datasets will be changed to lowercase.  Lahman's "gidp" will be renamed to "gdp" to match the abbreviation used in Retrosheet.  There are two Lahman field names that are not valid identifiers and these will be modified: 2B -> b_2b and 3B -> b_3b.

### Data Wrangling

Non-standard parsing of dates and times will be performed.  A heuristic to determine game start time will be used (as am/pm is missing).  Other custom data processing will be performed as needed.

Pandas datatypes will be optimized to save space and more accurately describe the attribute.  For example, the number of hits in a game is always between 0 and 255, so a uint8 can be used rather than an int64.  Likewise, for integer fields with missing values, the new Pandas Int64 (and its relatives) can be used instead of requiring a float datatype.

Datatype optimizations per column are persisted to disk for each corresponding csv file with the suffix `_types.csv`.  The function **from_csv_with_types()** and **to_csv_with_types()** are supplied to use the csv files with Pandas data types.

### Data Validation

pytest will be used to automate the running of data integrity tests, such as validating that the unique identifying fields are in fact, unique.

pytest:

* must be run from the `download_scripts` directory
* must be run after the scripts which download and parse the data have been run
* accepts custom option: --data-dir=<data_directory>
* accepts custom option: --runslow  # to run tests that depend on a slow to instantiate session fixture

### Data Consistency

To verify that the scripts worked correctly, the Retrosheet player per game and team per game data will be summarized to the yearly level and compared with Lahman.  This verification will be part of the supplied pytest tests.

### Statistics per Player Role

A baseball player may have several roles during the course of a game, such as batter, fielder, and pitcher.  Most attributes are unique to the role, but some are not.  The same player can hit a home run as a batter and allow a home run as a pitcher.

There are nine fielding roles.  For example, the same player could make a put-out while playing second base and later make a put-out while playing first base.

### Script Summary

cd to the download_scripts directory.  All scripts have help.   Scripts can be run as:

* `python lahman_download.py --help` or 
* `lahman_download.py --help` if the script has execute permission.

After the scripts have been run, pytest can be run to verify that the download succeeded and the data is fine.

For all scripts:

* -v for verbose: logs to stdout
* --log INFO:  appends to download.log file (at the INFO level)
* --data-dir ../data:   specifies that the data directory is a sibling of the download_scripts directory (or whatever directory you chose)

Scripts:

* **run_all_scripts.py** --data-dir=../data
  * convenience script to run all scripts with -v --log=INFO
* **lahman_download.py** -v --log=INFO --data-dir=../data
  * downloads all the lahman data and unzips it to `../data/lahman/raw`

* **lahman_wrangle.py** -v -log=INFO --data-dir=../data
  * converts field names to snake_case
  * performs custom parsing of dates
  * drops fielding columns that have more than 90% missing values
  * optimizes data types
  * persists with optimized data types to `../data/lahman/wrangle`
* **retrosheet_download.py** -v -log=INFO --data-dir=../data
  * downloads the retrosheet data and unzips it to `../data/retrosheet/raw`
  * by default, data is downloaded from 1955 through 2019 inclusive
  * this can be changed by using the --start-year and --end-year flags
* **retrosheet_parse.py** -v --log=INFO --data-type --data-dir=../data
  * with --data-type option
    * uses the precomputed optimized data type files at provided with this repo at `data/retrosheet`
    * this can save several Gigs of RAM, if data goes back to the 1950s or earlier
  * without --data-type option
    * will compute the optimized data types
    * may require more than 16 Gig of RAM, if data goes back to the 1950s or earlier
  * runs the cwdaily and cwgame parsers to generate csv files
    * cwdaily creates player per game statistics
    * cwgame creates team per game statistics
    * see the "Parsers for Retrosheet" section below
  * all data in the `data/retrosheet/raw` is parsed
  * collects the results into one DataFrame for cwdaily and one DataFrame for cwgame
  * converts the field names to lower case
  * drops columns that have more than 95% missing values
  * persists the results to `../data/retrosheet/collected`
  * the DataFrames are compressed using gzip
    * the compression ratio is about 18:1
* **retrosheet_datadictionary.py**
  * this is an optional script which produces the data dictionary for the generated csv files
  * script results are saved in `data/retrosheet` directory and are also available in this github repo
* **retrosheet_wrangle.py** -v --log=INFO --data-type --data-dir=../data
  *  custom parsing of game time
  * data cleanup for non-unique (player_id, game_id)
  * and more ...
* **tests/test_data.py**
  * after running the above scripts, run 'pytest' from the same directory
  * there are conftest.py and pytest.ini files for pytest
  * the "unit tests" used for data checking are in tests/test_data.py



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

The **cwgame** parser generates statistics per game for both teams

#### Retrosheet Data Dictionary

The retrosheet_datadictionary.py script will generate a description of the output of the cwdaily and cwgame parsers.

This script has been run and the descriptions have been saved to:  `data/retrosheet/cwdaily_datadictionary.txt` and `data/retrosheet/cwgame_datadictionary.txt`

### Parsers for Retrosheet

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

#### How to Build Retrosheet Parsers on Linux

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