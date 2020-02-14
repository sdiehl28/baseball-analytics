# Baseball Analytics

## Overview

Scripts are provided which download, parse, and wrangle the Lahman and Retrosheet open-source data to produce a set of tidy csv files that can be analyzed in Python and Pandas, or R.  There is also an optional script to load the data into Postgres.

Examples of data analysis are provided using using Python and Pandas in Jupyter Notebooks.

The value of publishing the scripts and the analysis is that the results are repeatable.  The precise data used and the precise data processing, are made available for anyone to use, modify and evaluate.

The value of wrangling the data is that the analysis is much easier and the RAM and storage requirements are much less.

## Data Science and Sabermetrics

[Sabermetrics](https://en.wikipedia.org/wiki/Sabermetrics) was created before the advent of modern software tools for data analysis and fast personal computers. One aim is to create metrics that make it easy for people to quickly grasp how much a baseball player contributes to his team's wins. In data science terminology, this is an example of explanatory modeling.

Another aim of Sabermetrics is to identify metrics that are likely to be useful in a predictive model.  In data science terminology, a baseball domain expert uses feature engineering to create inputs (Sabermetrics) to improve predictive accuracy.

Data Science, and science in general, must produce results that can be repeated by others. See [Reproducible Research](https://en.wikipedia.org/wiki/Reproducibility#Reproducible_research). A problem with many Sabermetric blog posts is that the results cannot be repeated because the code use to perform the analysis, and the data itself, are not made public.

The emphasis here is on repeatable data analysis. The scripts to download the data are provided. The data is wrangled to simplify the analysis, and the data wrangling scripts are provided. Over 50 tests are also provided to verify the data wrangling, verify the Retrosheet parsers, and determine how consistent the Retrosheet data is with the Lahman data. These tests can be run with the single command, 'pytest'. The data analysis is published in unambiguous code in the form of Jupyter notebooks.

### Data Preparation Scripts

The Python scripts prepare the data for analysis, including running the open-source [Retrosheet Parsers](https://github.com/sdiehl28/baseball-analytics/blob/master/RetrosheetParsers.md). These scripts are at [download_scripts](https://github.com/sdiehl28/baseball-analytics/tree/master/download_scripts).

### Data Analysis

Examples of baseball analysis are presented using Jupyter Notebooks with Python, Pandas and matplotlib/seaborn plots.

Some initial analysis includes:

- How many more runs per game are there when the DH is used? Could this difference be due to chance?
- How has game length and pitcher count increased over the years?
- - How is game length related to pitcher count? Could this relationship be due to chance?
- Computing the Park Factor
- - What did ESPN, Fangraphs, and others get wrong about the park factor for Fenway Park in 2019?
  - Demonstrate that accounting for each team's road schedule will strongly affect the home park factor, for a few teams each year.
  - Compute the game-weighted average Park Factor on the road, for each team, for several years.
- Linear Modeling of Runs per Half Inning
  - How much does a singe, double, triple and home run contribute to run scoring per half-inning?

These Jupyter Notebooks are in this repo at: [Baseball Analysis](https://github.com/sdiehl28/baseball-analytics/tree/master/baseball_jupyter_nb).

### Data Validation

pytest is used to automate data integrity and data consistency testing. More than 50 tests check more than 100 attributes. The data is checked for all years between 1974 and 2019, as this is the period for which there is no missing Retrosheet data.

Some examples:

- the number of home runs hit by batters should equal the number of home runs allowed by pitchers
- when the Retrosheet data is aggregated to the same level as the Lahman data and compared, the results should be close
- fields which should uniquely identify a row in a csv file, actually do.

The data consistency tests show that the [Retrosheet parsers](https://github.com/sdiehl28/baseball-analytics/blob/master/RetrosheetParsers.md), are 100% self-consistent. In other words, when the data from one Retrosheet parser is aggregated to the same level as another Retrosheet parser and compared, the results are identical.

The data consistency tests show that the Lahman data is almost 100% self-consistent. In other words, when data from one Lahman csv file is aggregated to the same level as another and compared, the results are almost identical.

The data consistency tests show that the Retrosheet data when aggregated and compared with the Lahman data over the period 1974 through 2019 is:

- for batting stats: within 0.01%
- for pitching stats: within 0.06%
- for fielding stats: within 0.8%

For a detailed description of many of the data consistency tests, see my Jupyter notebook [Data Consistency](https://nbviewer.jupyter.org/github/sdiehl28/baseball-analytics/blob/master/baseball_jupyter_nb/02_Data_Consistency_CSV.ipynb)

### Ongoing

Additional examples of baseball data analysis are continually being added.

Retrosheet postseason data will soon be parsed and wrangled. All Retrosheet regular season data has been parsed and wrangled.

## Tidy Data Definition

Data is [tidy](https://en.wikipedia.org/wiki/Tidy_data) if:

1. Each variable forms a column.
2. Each observation forms a row.
3. Each type of observational unit forms a table or csv file.

## MLB Data Wrangling

Two excellent sources of free baseball data are:

- Lahman
- Retrosheet

The Lahman data is tidy and is therefore easy to analyze, however the data is per season rather than per game. Finding a team's win streaks, a player's best month for hitting, and similar is not possible with the Lahman data.

The raw Retrosheet data is play-by-play data and is not in csv format. Three Retrosheet parsers are automatically run and their output is wrangled to create tidy csv files.

Having both Lahman and Retrosheet data allows for queries such as what was the longest hitting streak for all players who earned in the top 10% of salary that year.

The purpose of data wrangling is to make data analysis easier and more efficient. The 50+ data consistency tests would have been much more difficult to write had the data not been wrangled first.

The scripts which wrangle the Lahman and Retrosheet data will:

- ensure that for all csv files in both datasets, the same 50+ field names are used to represent the same information

- - for example, if a batter hits a "hr", then the opposing pitcher gave up a "hr" and "hr" is the field name used in the batting and pitching csv files for both Lahman and Retrosheet

- ensure that field names conform to official baseball abbreviations as much as possible

- - with the caveat that all field names must be valid Python identifiers and valid SQL column names

- determine the most efficient data type, for both Pandas and SQL, and persist that data type for each field in a corresponding csv file

- - this greatly reduces the amount of memory required and the amount of storage required in a database
  - code is provided to read/write csv files with persisted data types

- automate the running of the Retrosheet parsers and tidy their output

- - the majority of data tidying is to restructure the output of cwdaily to match that of Lahman by creating batting, pitching and fielding csv files per player per game.

- identify primary keys and sum statistics for the exceptionally few players who had multiple records with the same primary key

  - since 1948, the only duplicate key was produced by cwdaily in which a player had two rows created for one game

At this time, the wrangled data is not provided in this repo, only the scripts to create it are provided.

## Additional Information

For more information about the Lahman and Retrosheet data sets and how they were wrangled, see: [MLB Data Overview](https://github.com/sdiehl28/baseball-analytics/blob/master/MLB_Data_Overview.md)

For the data sources and their licenses see: [MLB Data Details](https://github.com/sdiehl28/baseball-analytics/blob/master/MLB_Data_Details.md)

## Development Environment

Clone the repo: `git clone https://github.com/sdiehl28/baseball-analytics.git`

Active your conda environment.  If creating a new conda environment, run `conda install anaconda`.  If using Postgres, also run `conda install psycopg2`

The scripts and Jupyter Notebooks were testing using Python 3.7 and Pandas 1.0.1 in a full [Anaconda](https://www.anaconda.com/distribution/) 2019.10 environment.

The [open-source parsers](https://sourceforge.net/projects/chadwick/) for Retrosheet must be installed to run the scripts. See: [Retrosheet Parsers](https://github.com/sdiehl28/baseball-analytics/blob/master/RetrosheetParsers.md).

