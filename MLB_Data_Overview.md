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

The **cwdaily** parser will generate a csv file with a row **per player per game**.  If data is collected since 1955, this will produce over 3 million rows with over 150 attributes.  These attributes include all attributes for all roles a player may have, including batter, pitcher, and all 9 fielding positions.  As players do not take on all roles in each game, almost all attribute values are zero.  

The output from cwdaily will be restructured into **batting stats per player per game**, **pitching stats per player per game** and **fielding stats per player per game** with a row created only if there are relevant stats for that player and game.  This is very similar to how the Lahman data is structured.

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

pytest will be used to automate the running of more than 50 data integrity and data consistency tests.  Tests include validating that the unique identifying fields for a csv file, are in fact unique.

Running pytest:

* recommend: 'pytest -v'
* must be run from the `download_scripts` directory
* must be run after the scripts which download and parse the data have been run
* accepts custom option: --data-dir=<data_directory>

If you like, you may spot check the data using [Baseball Reference](https://www.baseball-reference.com/).  Baseball Reference uses the Retrosheet data.  The box score for a game can be constructed from the game_id using: `'https://www.baseball-reference.com/boxes/' + game_id[:3] + '/' + game_id + '.shtml'` For example, to verify that there are two entries for Chris Young for game_id = BOS201708250, the url is: https://www.baseball-reference.com/boxes/BOS/BOS201708250.shtml

### Data Consistency

The data consistency tests ensure that over 100 common attributes between Lahman and Retrosheet are within 1% of each other when aggregated (summed) to the same level between the years 1974 and 2019.  Most aggregated attributes differ by less than 0.1%.  These tests are run on the wrangled data.

This shows that the Lahman and Retrosheet data sets are consistent with each other and that the scripts worked correctly.

### Baseball Player Roles

A baseball player may have several roles during the course of a game, such as batter, pitcher and any of the 9 fielding positions.

Attribute names for batters and pitchers are the same where it makes sense to do so.  For example, if a batter hits a "hr" then then opposing team's pitcher must have given up a "hr".

All attribute names for the 9 fielding positions are identical, even though passed-ball and catcher-interference only apply to the catcher.  This allows for a single csv file for fielding with no null values.
