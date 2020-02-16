## MLB Data Overview

### Tidy Data Definition

Data is [tidy](https://en.wikipedia.org/wiki/Tidy_data) if:

1. Each variable forms a column.
2. Each observation forms a row.
3. Each type of observational unit forms a table or csv file.

The above is nearly identical to the database term "3rd normal form".  Arguably the last rule above is not required for data analysis, but it saves space and helps to ensure data consistency.

The benefit of making the data tidy is that data analysis is much easier.

### Lahman Overview

The Lahman data is tidy.  The description of these csv files is in the `data/lahman` directory and is called readme2017.txt.  It was copied from the Lahman website and it is accurate for 2018 and 2019 as well.

A description of data might be called a "data dictionary" or a "code book" or simply just a "readme.txt".

As of December 2019, Lahman has data through the end of the 2019 season.  

### Retrosheet Overview

The Retrosheet data is not tidy nor is it in csv format, rather it is in a custom text format.  Reading this format is most easily done using the open-source parsers by Dr. T. L.  Turocy which convert the Retrosheet text files into csv files with a header row.

As of December 2019, Retrosheet has data through the 2019 season.

### Field Names

The field names in both datasets are based on standard baseball abbreviations.  See for example https://en.wikipedia.org/wiki/Baseball_statistics.

The field names have been changed as little as possible to remain familiar.  Field name changes include:

* columns in different csv files with the same meaning, now have the same column name
* CamelCase is converted to snake_case
* '2B' and '3B' are changed to 'double' and 'triple' to make them valid identifiers
* Retrosheet's 'gdp' is changed to 'gidp' to match Lahman
* Retrosheet's 'hp' is changed to 'hbp' to match Lahman 

### CSV Files Created

After data wrangling, the following csv files exist:

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

### Unique Identifiers (Primary Keys)

When performing data analysis, it is essential to know what field(s) uniquely identify a row in a csv file (or table).  It turns out that cwgame generates the equivalent of two entries for the "box score" one time since 1948.  These two entries were summed appropriately so that the expected unique identifiers work properly.

Not having unique identifiers greatly complicates data analysis.

### Data Types

There are several reasons to pay close attention to the data types used by Pandas and/or Postgres:

* the data type provides information about the field
* the data type helps to ensure correct code
* use the smallest appropriate data type saves memory and database storage

For example, the default value for an integer in Pandas is 'int64', and yet the maximum number of hits in a game can be saved in just 8 bits with a 'uint8'.  Pandas nullable integer data types are also made use of.

Data type optimization per column per csv file are persisted to disk by writing a corresponding csv files with the suffice _types.csv.  I have written python function which then read the csv back into a dataframe using the optimized persisted data types.

## Data Wrangling

The scripts which wrangle the Lahman and Retrosheet data will:

* ensure that the same field name has the same meaning across all csv files for both Lahman and Retrosheet
* ensure that the field names conform to official baseball abbreviations as much as possible
  * with the caveat that all field names must be valid Python identifiers and valid SQL column names
* determine the most efficient data type, for both Pandas and Postgres tables, and persist that data type for each corresponding csv file
* automate the running of 3 Retrosheet parsers and tidy the output
* translate numeric codes into text so they can be understood
* identify the different ways in which missing data is represented and create the appropriate value in Pandas
* translate unusual date and time representations to appropriate data and time Pandas data types
* normalize the data
  * for example, every player does not play every fielding position in every game, and yet that is how the output of the cwgame parsers presents the data.  As such, that output is almost all zeros.  A better representation is to create a row for each player for each fielding position they actually played  in a game.
* and more ...

### Baseball Player Roles

A baseball player may have several roles during the course of a game, such as batter, pitcher and any of the 9 fielding positions.

Attribute names for batters and pitchers are the same where it makes sense to do so.  For example, if a batter hits a "hr" then then opposing team's pitcher must have given up a "hr".

All attribute names for the 9 fielding positions are identical, even though passed-ball only applies to the catcher and interference is mostly relevant to the catcher, pitcher and first baseman.  This allows for a single csv file for fielding with no null values.