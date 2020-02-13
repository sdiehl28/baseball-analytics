# Baseball Analytics

## Overview

The free and open-source baseball data sets from Lahman and Retrosheet are downloaded, parsed, wrangled, and analyzed.

## Sabermetrics

[Sabermetrics](https://en.wikipedia.org/wiki/Sabermetrics) is a term coined before the advent of modern software tools for data analysis and fast personal computers. One aim is to create metrics that make it easy for people to quickly grasp how much a player contributes to his team's wins. In data science terminology, this is an example of explanatory modeling.

Another aim of Sabermetrics is to identify metrics that are likely to be predictive. In data science terminology, this is an example of predictive modeling in which a domain expert uses feature engineering to create inputs (Sabermetrics) to improve predictive accuracy.

Data Science, and science in general, must produce results that are repeatable. See for example: [Reproducible Research](https://en.wikipedia.org/wiki/Reproducibility#Reproducible_research). A problem with many Sabermetric blog posts is that the results cannot be reproduced because the queries that created them are not published.

The emphasis here is on repeatable data analysis. The scripts to download the data are provided.  The data is wrangled to simplify the analysis and the data wrangling scripts are provided. Over 50 tests are also provided to verify the data wrangling, verify the Retrosheet parsers and determine how consistent the Retrosheet data is with the Lahman data. These tests can be run with the single command, 'pytest'. The data analysis is published in unambiguous code in the form of Jupyter notebooks.

### Data Preparation

The Python scripts prepare the data for analysis, including running the open-source [Retrosheet Parsers](https://github.com/sdiehl28/baseball-analytics/blob/master/RetrosheetParsers.md). These scripts are located in this repo at: [download_scripts](https://github.com/sdiehl28/baseball-analytics/tree/master/download_scripts).

A script is also provided to load the wrangled data into Postgres with primary and foreign key constraints. The use of Postgres is optional.

### Data Analysis

Examples of baseball analysis questions are answered using Jupyter Notebooks with Python, Pandas and matplotlib/seaborn plots.

Some initial questions include:

- How many more runs per game are there when the DH is used? Could this difference be due to chance?
- How has game length and pitcher count increased over the years?
- - How is game length related to pitcher count? Could this relationship be due to chance?
- Computing the Park Factor
- - What did ESPN, Fangraphs, and others get wrong about the park factor for Fenway Park in 2019?
  - Demonstrate that accounting for each team's road schedule will strongly affect the home park factor, for a few teams each year.
- Linear Modeling of Runs per Half Inning
  - How much does a singe, double, triple and home run contribute to run scoring per half-inning?

These Jupyter Notebooks are in this repo at: [Baseball Analysis](https://github.com/sdiehl28/baseball-analytics/tree/master/baseball_jupyter_nb).

### Data Validation

pytest is used to automate data integrity and data consistency testing. More than 50 tests check more than 100 attributes. The data is checked for all years between 1974 and 2019, as this is the period for which there is no missing Retrosheet data.

Some examples:

- the number of home runs hit by batters should equal the number of home runs allowed by pitchers
- when the Retrosheet data is aggregated to the same level as the Lahman data and compared, the results should be close
- fields which should uniquely identify a row in a CSV file, actually do.

The data consistency tests show that the [Retrosheet parsers](http://chadwick.sourceforge.net/doc/index.html), when run against the Retrosheet data, are 100% self-consistent. In other words, when the data from one Retrosheet parser is aggregated to the same level as another Retrosheet parser and compared, the results are identical.

The data consistency tests show that the Lahman data is almost 100% self-consistent. In other words, when data from one Lahman CSV file is aggregated to the same level as another and compared, the results are almost identical.

The data consistency tests show that the Retrosheet data when aggregated and compared with the Lahman data over the period 1974 through 2019 is:

- for batting stats: within 0.01%
- for pitching stats: within 0.06%
- for fielding stats: within 0.8%

For a detailed description of many of the data consistency tests, see my Jupyter notebook [Data Consistency](https://nbviewer.jupyter.org/github/sdiehl28/baseball-analytics/blob/master/baseball_jupyter_nb/02_Data_Consistency_CSV.ipynb)

### Ongoing

Additional examples of baseball data analysis are continually being added.

Retrosheet postseason data will soon be parsed and wrangled. All Retrosheet regular season data has been parsed and wrangled.

## MLB Data Wrangling

The two best sources of free baseball data are:

- Lahman
- Retrosheet

The Lahman data is tidy and is therefore easy to analyze with Pandas or SQL, however the data is per season rather than per game. Finding a team's win streaks, a player's best month for hitting, and similar is not possible with the Lahman data.

The raw Retrosheet data is play-by-play data and is not in CSV format. The Retrosheet parsers perform the following:

- **cwevent** produces a CSV file with a row per play (aka event)
- **cwdaily** produces a CSV file with a row per player per game
- **cwgame** produces a CSV file with a row per game

Having both Lahman and Retrosheet data allows for queries such as what was the longest hitting streak for all players who earned in the top 10% of salary that year.

The purpose of data wrangling is to make data analysis easier and more efficient. The 50+ data consistency tests would have been much more difficult to write had the data not been wrangled first.

The scripts which wrangle the Lahman and Retrosheet data will:

- ensure that for all CSV files in both datasets, the same 50+ field names are used to represent the same information

- - for example, if a batter hits a "hr", then the opposing pitcher gave up a "hr" and "hr" is the field name used in the batting and pitching CSV files for both Lahman and Retrosheet

- ensure that field names conform to official baseball abbreviations as much as possible

- - with the caveat that all field names must be valid Python identifiers and valid SQL column names

- determine the most efficient data type, for both Pandas and SQL, and persist that data type for each field in a corresponding CSV file

- - this greatly reduces the amount of memory required and the amount of storage required in a database
  - code is provided to read/write CSV files with persisted data types

- automate the running of the Retrosheet parsers and tidy their output

- - the majority of data tidying is to restructure the output of cwdaily to match that of Lahman by creating batting, pitching and fielding csv files per player per game.

- identify primary keys and sum statistics for the exceptionally few players who had multiple records with the same primary key

  - since 1948, the only duplicate key was produced by cwdaily in which a player had two rows created for one game

At this time, the wrangled data is not provided in this repo, only the scripts to create it are provided.

## Development Environment

The scripts and Jupyter Notebooks were testing using Python 3.7 in a full [Anaconda](https://www.anaconda.com/distribution/) 2019.10 environment. Note that the [open-source parsers](https://sourceforge.net/projects/chadwick/) for Retrosheet must be installed to run the scripts. See: [Retrosheet Parsers](https://github.com/sdiehl28/baseball-analytics/blob/master/RetrosheetParsers.md).

## Additional Information

For more information about the Lahman and Retrosheet data sets and how they were wrangled, see: [MLB Data Overview](https://github.com/sdiehl28/baseball-analytics/blob/master/MLB_Data_Overview.md)

For the data sources and their licenses see: [MLB Data Details](https://github.com/sdiehl28/baseball-analytics/blob/master/MLB_Data_Details.md)