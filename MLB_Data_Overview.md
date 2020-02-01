## MLB Data Overview

### Lahman Overview

The Lahman data is tidy.  The latest description of each csv file has been copied from the Lahman website to the `data/lahman` directory in this repo and is called readme2017.txt.  Loosely speaking, a description of data might be called "readme" or "data dictionary" or "code book".

As of December 2019, Lahman has data through the end of the 2019 season.  

Data is tidy if:

1. Each variable forms a column.
2. Each observation forms a row.
3. Each type of observational unit forms a table or csv file.

### Retrosheet Overview

The Retrosheet data is not tidy nor is it in CSV format.  Retrosheet has all play-by-play data for every MLB game since 1974.  Data is available since 1918 with older years having somewhat more missing data.  Open source parsers from Dr. T. L. Turocy will be used to parse and summarize the play-by-play data.

The description of the column headings for the parser generated csv files has been created and copied to `data/retrosheet` as cwdaily_datadictionary.txt and cwgame_datadictionary.txt.

As of December 2019, Retrosheet has data through the 2019 season.

### Field Names

The field names in both datasets are based on standard baseball abbreviations.  See for example: https://en.wikipedia.org/wiki/Baseball_statistics.

The field names have been changed as little as possible to remain familiar.  Field name changes include:

* columns in different CSV files with the same meaning, now have the same column name
* CamelCase is converted to snake_case
* '2B' and '3B' are changed to 'double' and 'triple' to make them valid identifiers
* Retrosheet's 'gdp' is changed to 'gidp' to match Lahman
* Retrosheet's 'hp' is changed to 'hbp' to match Lahman 

### Data Wrangling

After data wrangling, the following CSV files exist:

**Lahman**

* Stats per Player per Year:
  * batting.csv
  * pitching.csv
  * fielding.csv
* Postseason Stats per Round per Player per Year
  * battingpost.csv
  * pitchingpost.csv
  * fieldingpost.csv
* Stats per Team per Year:
  * teams.csv -- contains team_id for both Lahman and Retrosheet
* Other
  * people.csv -- contains player_id for Lahman, Retrosheet and Baseball-Reference
  * salaries.csv
  * parks.csv
  * more to be added soon ...
  

**Retrosheet**  

* Stats per Event
  * event.csv.gz
* Stats per Player per Game:
  * batting.csv.gz
  * pitching.csv.gz
  * fielding.csv.gz
* Stats per Team per Game:
  * team_game.csv.gz
* Stats per Game:
  * game.csv.gz
* Postseason stats: to be added soon ...

A script to create Postgres tables with appropriate primary key constraints and load each of the above csv files into these tables is provided.

Where necessary, statistics will be summed so that "primary keys" are unique.  Extremely few records require this summing but as most data processing relies on having a set of fields which uniquely identify a record, this is required.

Pandas datatypes will be optimized to save space and more accurately describe the attribute.  For example, the number of hits in a game is always between 0 and 255, so a uint8 can be used rather than an int64.  Likewise, for integer fields with missing values, the new Pandas Int64 (and similar) can be used instead of requiring a float datatype.  Similarly, the database table create statements for optional use with a database, use data types optimized to reduce storage.

Datatype optimizations per column are persisted to disk for each corresponding csv file with the suffix `_types.csv`.  The Python functions **from_csv_with_types()** and **to_csv_with_types()** have been written to  allow persistence of data to/from csv files without losing data type information.

### Baseball Player Roles

A baseball player may have several roles during the course of a game, such as batter, pitcher and any of the 9 fielding positions.

Attribute names for batters and pitchers are the same where it makes sense to do so.  For example, if a batter hits a "hr" then then opposing team's pitcher must have given up a "hr".

All attribute names for the 9 fielding positions are identical, even though passed-ball only applies to the catcher and interference is mostly relevant to the catcher, pitcher and first baseman.  This allows for a single csv file for fielding with no null values.