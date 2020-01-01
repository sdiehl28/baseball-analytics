# Baseball Analytics
There are two primary sources of free and extensive baseball data:

* Lahman
* Retrosheet

The Lahman data is tidy and is therefore easy to use with Pandas or SQL, however the data is per season rather than per game.  Finding a team's win streaks, a player's best month for hitting, and similar is not possible with the Lahman data.

The Retrosheet data is play-by-play data which is arguably too fine grained and must be parsed and summarized to the game level.  To make it easy to use, it must be made tidy.

Having both data sets available allows for queries such as what was the longest hitting streak for all players who earned in the top 10% of salary that year.

The scripts in this repo will wrangle the Lahman and Retrosheet data to create csv files to:

* allow for easy Pandas analysis (or SQL analysis if loaded into a database)
* allow both data sets to be referenced in the same query
* ensure that for both data sets, the same 50+ field names are used to represent the same information
  * for example, if a batter hits a "hr", then the opposing pitcher gave up an "hr" and "hr" is the field name used in the batting and pitching csv files for both Lahman and Retrosheet
* ensure that field names conform to official baseball abbreviations
* ensure that all field names are valid Python identifiers and valid SQL column names
* determine the most efficient data type, for both Pandas and SQL, and persist that data type for each field in a corresponding csv file
  * code is provided to read/write csv files with persisted data types
* parse the Retrosheet data using open-source parsers (which on Linux must be built from source code)
* tidy the Retrosheet data, clean primary key data to be unique, and identify primary and foreign keys
* ensure that the data is accurate by providing more than 25 pytest tests to verify that the restructured data is consistent between the two data sets, the primary keys are unique, etc.  

TODO: scripts to load the csv files, with primary and foreign key constraints and optimal data types into Postgres are currently being worked on.

TODO: Examples of baseball data analysis will be provided in the form of Jupyter Notebooks.

At this time, the restructured data is not provided in this repo, only the scripts to create it are provided.

If you have any questions, you may send me an email with the word "baseball" in the subject to: sdiehl28@gmail.com

## Environment

The scripts were tested using Python 3.7 in a full [Anaconda](https://www.anaconda.com/distribution/) 2019.10 environment.  The [open-source parsers](https://sourceforge.net/projects/chadwick/) for Retrosheet must be installed to run the scripts.  See: [Parsers for Retrosheet](#Parsers-for-Retrosheet) below.

## MLB Data Overview

### Lahman Overview

Lahman has MLB statistics summarized **per player per year** and **per team per year**.

The Lahman data is tidy.  The latest description of each csv file has been copied from the Lahman website to the `data/lahman` directory in this repo and is called readme2017.txt.  Loosely speaking, a description of data might be called "readme" or "data dictionary" or "code book".

As of December 2019, Lahman has data through the end of the 2019 season.  

Data is tidy if:

1. Each variable forms a column.
2. Each observation forms a row.
3. Each type of observational unit forms a table or csv file.

### Retrosheet Overview

Retrosheet has play-by-play data for every MLB game since 1974.  Data is available since 1918 with older years having somewhat more missing data.  Open source parsers from Dr. T. L. Turocy will be used to parse and summarize the play-by-play data.

The **cwdaily** parser will generate a csv file with a row **per player per game**.  If data is collected since 1955, this will produce over 3 million rows with over 150 attributes.  These attributes include all attributes for all roles a player may have, including batter, pitcher, and all 9 fielding positions.  As players do not take on all roles in each game, almost all attribute values are zero.  The output from cwdaily will be restructured into **batting stats per player per game**, **pitching stats per player per game** and **fielding stats per player per game** with a row created only if there are relevant stats for that player and game.  This is very similar to how the Lahman data is structured.

The **cwgame** parser will generate a csv file with a row that has stats for both teams per game as well as game specific stats such as attendance.  This output will be restructured into stats **per team per game** and stats **per game**.

The description of the column headings for the parser generated csv files has been created and copied to `data/retrosheet` as cwdaily_datadictionary.txt and cwgame_datadictionary.txt.

As of December 2019, Retrosheet has data through the 2019 season.

### Field Names

The field names in both datasets are based on standard baseball statistic abbreviations.  See for example: https://en.wikipedia.org/wiki/Baseball_statistics.

The field names have been changed as little as possible to remain familiar.  Field name changes include:

* columns in different csv files with the same meaning, now have the same column name
* CamelCase is converted to snake_case
* '2B' and '3B' are changed to 'double' and 'triple' to make them valid identifiers
* Retrosheet's 'gdp' is changed to match Lahman's 'gidp'
* Retrosheet's 'hp' is changed to match Lahman's 'hbp' 

### Data Wrangling

Retrosheet data is restructured.  Custom parsing of dates and times is performed.  And more.

Data will be cleaned so that "primary keys" are unique.  Extremely few records require this type of cleaning, but as most data processing relies on having a set of fields which uniquely identify a record, this cleaning is required.

Pandas datatypes will be optimized to save space and more accurately describe the attribute.  For example, the number of hits in a game is always between 0 and 255, so a uint8 can be used rather than an int64.  Likewise, for integer fields with missing values, the new Pandas Int64 (and similar) can be used instead of requiring a float datatype.

Datatype optimizations per column are persisted to disk for each corresponding csv file with the suffix `_types.csv`.  The Python functions **from_csv_with_types()** and **to_csv_with_types()** have been written to  allow persistence of data to/from csv files without losing data type information.

### Data Validation

pytest will be used to automate the running of more than 25 data integrity and data consistency tests.  Tests include validating that the unique identifying fields for a csv file, are in fact unique.

Running pytest:

* recommend: 'pytest -v'
* must be run from the `download_scripts` directory
* must be run after the scripts which download and parse the data have been run
* accepts custom option: --data-dir=<data_directory>

### Data Consistency

The data consistency tests ensure that over 100 common attributes between Lahman and Retrosheet are within 1% of each other when aggregated (summed) to the same level between the years 1974 and 2019.  Most aggregated attributes differ by less than 0.1%.  These tests are run on the wrangled data.

This shows that the Lahman and Retrosheet data sets are consistent with each other and that the scripts worked correctly.

### Baseball Player Roles

A baseball player may have several roles during the course of a game, such as batter, pitcher and any of the 9 fielding positions.

Attribute names for batters and pitchers are the same where it makes sense to do so.  For example, if a batter hits a "hr" then then opposing team's pitcher must have given up a "hr".

All attribute names for the 9 fielding positions are identical, even though passed-ball and catcher-interference only apply to the catcher.  This allows for a single csv file for fielding with no null values.

## Script Summary

Scripts are run from the download_scripts directory.  For more detail about the scripts, see the README.md in the github download_scripts directory: [download_scripts](https://github.com/sdiehl28/baseball-analytics/tree/master/download_scripts)

Options include:

* -v for verbose which logs to stdout
* --log=INFO which logs (at the INFO level) to download.log
* --data-dir=../data which specifies the data directory (default is ../data)

Scripts with example command line arguments:

* **run_all_scripts.py** --data-dir=../data --start-year=1955 --end-year=2019
  * convenience script to run all scripts in the proper order
* **lahman_download.py** -v --log=INFO --data-dir=../data
  * downloads all the lahman data and unzips it to `../data/lahman/raw`

* **lahman_wrangle.py** -v -log=INFO --data-dir=../data
  * wrangles the Lahman data and persists it with optimized data types to `../data/lahman/wrangle`
* **retrosheet_download.py** -v -log=INFO --data-dir=../data --start-year=1955 --end-year=2019
  * downloads the Retrosheet data and unzips it to `../data/retrosheet/raw`
  * pytest data consistency tests use data between 1974 and 2019, so --start-year should be 1974 or earlier and --end-year should be 2019 (or later when 2020 data becomes available)
* **retrosheet_parse.py** -v --log=INFO --use-datatypes --data-dir=../data
  * parses the play-by-play data using the cwdaily and cwgame open-source parsers
    * see [Parsers for Retrosheet](#Parsers-for-Retrosheet) below
    * all data in `data/retrosheet/raw` is parsed with the results placed in `data/retrosheet/parsed`
  * all parsed data is collected into a one DataFrame for cwdaily and one DataFrame for cwgame and placed in `data/retrosheet/collected`
* **retrosheet_wrangle.py** -v --log=INFO --data-dir=../data
  *  wrangles the collected Retrosheet data and persists it with optimized data types to `../data/retrosheet/wrangle`
* **pytest -v**
  * runs the functional, data consistency and data integrity tests from tests/test_func.py and tests/test_data.py

## MLB Data Details

### Lahman Data Source

The most recent data will be downloaded from:  https://github.com/chadwickbureau/baseballdatabank/archive/master.zip

**Lahman Data License** from https://github.com/chadwickbureau/baseballdatabank readme.txt

```
This work is licensed under a Creative Commons Attribution-ShareAlike
3.0 Unported License.  For details see:
http://creativecommons.org/licenses/by-sa/3.0/
```

#### Lahman Data Dictionary

The most recent data dictionary is:  http://www.seanlahman.com/files/database/readme2017.txt  

This file is also copied to this repo at: `data/lahman/readme2017.txt`

### Retrosheet Data Source

The play-by-play data will be downloaded for each year at: http://www.retrosheet.org/events/{year}eve.zip

The retrosheet_download script will put these in: `../data/retrosheet/raw`

**Retrosheet Data License** from https://www.retrosheet.org/notice.txt 

```
     The information used here was obtained free of
     charge from and is copyrighted by Retrosheet.  Interested
     parties may contact Retrosheet at "www.retrosheet.org".
```

#### Parser Generated CSV Files

The csv files must be generated by parsing the play-by-play data files.  The scripts will put the parsed csv files in:  `../data/retrosheet/parsed`.

The **cwdaily** parser generates statistics per player per game.  Attributes are prefixed by b for batter, p for pitcher and f_{pos} for fielder where pos is one of P, C, 1B, 2B, 3B, SS, LF, CF, RF.

The **cwgame** parser generates statistics per game for both teams.

#### Retrosheet Data Dictionary

The retrosheet_datadictionary.py script will generate a description of the output of the cwdaily and cwgame parsers.

This script has been run and the descriptions have been saved to:  `data/retrosheet/cwdaily_datadictionary.txt` and `data/retrosheet/cwgame_datadictionary.txt`

## Parsers for Retrosheet

The open source parsers created by Dr. T. L. Turocy will be used.

**Retrosheet Parsers License** from https://github.com/chadwickbureau/chadwick README

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