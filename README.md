# Baseball Analytics

## Overview

Scripts are provided which download, parse, and wrangle the Lahman and Retrosheet data to produce a set of tidy csv files that can be analyzed in Python and Pandas, or R.  There is also an optional script to load the data into Postgres.

Examples of data analysis are provided using Python and Pandas in Jupyter Notebooks.

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

### Data Validation and Wrangling Validation

There is no way to know the accuracy of the Retrosheet play-by-play data, but it is assumed to be quite accurate given the large number of volunteers who have worked on it for decades.

The Lahman data was originally gathered at the season level independently of the Retrosheet data and is therefore inconsistent with Retrosheet in some cases.  For the last few years it appears the Lahman seasonal data is derived from the Retrosheet data so there are no new discrepancies.  Lahman also includes data not in Retrosheet, such as player's salaries.

The following data checks can be made:

* how close is the Retrosheet data to the Lahman data
* how consistent is the data produced by three Retrosheet parsers with each other
* how consistent is the data in the Lahman tables

Performing these checks on the wrangled data also verifies the wrangling (data restructuring) code did not change the data.

pytest is used to automate more than 50 tests which check more than 100 attributes. The data is checked for all years between 1974 and 2019, as this is the period for which there is no missing Retrosheet data.

The data consistency tests show that the [Retrosheet parsers](https://github.com/sdiehl28/baseball-analytics/blob/master/RetrosheetParsers.md), are 100% self-consistent. In other words, when the data from one Retrosheet parser is aggregated to the same level as another Retrosheet parser and compared, the results are identical.  This shows that there are no errors in the parsers, and no errors in my restructuring of the parser output.

The data consistency tests show that the Lahman data is almost 100% self-consistent. For example, when the data in batting is aggregated to the team level and compared with the batting data in teams, the results are almost identical.

The data consistency tests show that the Retrosheet data when aggregated and compared with the Lahman data over the period 1974 through 2019 is:

- for batting stats: within 0.01%
- for pitching stats: within 0.06%
- for fielding stats: within 0.8%

For a detailed description of many of the data consistency tests, see my Jupyter notebook [Data Consistency](https://nbviewer.jupyter.org/github/sdiehl28/baseball-analytics/blob/master/baseball_jupyter_nb/02_Data_Consistency_CSV.ipynb)

### Ongoing

Additional examples of baseball data analysis are continually being added.

Retrosheet postseason data will soon be parsed and wrangled. All Retrosheet regular season data has been parsed and wrangled.

## Additional Information

For more information about the Lahman and Retrosheet data sets and how they were wrangled, see: [MLB Data Overview](https://github.com/sdiehl28/baseball-analytics/blob/master/MLB_Data_Overview.md)

For the data sources and their licenses see: [MLB Data Details](https://github.com/sdiehl28/baseball-analytics/blob/master/MLB_Data_Details.md)

## Development Environment

Clone the repo: `git clone https://github.com/sdiehl28/baseball-analytics.git`

Active your conda environment.  If creating a new conda environment, run `conda install anaconda`.  If using Postgres, also run `conda install psycopg2`

The scripts and Jupyter Notebooks were testing using Python 3.7 and Pandas 1.0.1 in a full [Anaconda](https://www.anaconda.com/distribution/) 2019.10 environment.

The [open-source parsers](https://sourceforge.net/projects/chadwick/) for Retrosheet must be installed to run the scripts. See: [Retrosheet Parsers](https://github.com/sdiehl28/baseball-analytics/blob/master/RetrosheetParsers.md).

