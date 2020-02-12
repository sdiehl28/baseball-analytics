## Jupyter Notebooks

The Jupyter Notebooks:

* with a CSV suffix uses CSV files as the data source
* with a SQL suffix uses SQL to to perform the same analysis

The links below will display the notebook using nbviewer:  

- [01_Intro_CSV](https://nbviewer.jupyter.org/github/sdiehl28/baseball-analytics/blob/master/baseball_jupyter_nb/01_Intro_CSV.ipynb)  
  - how has game length increased over the years?
  - how has pitcher count increased over the years?
  - what it the relationship between pitcher count and game length?
  - how many more runs are scored in games for which the DH is used?
- [01_Intro_SQL](https://nbviewer.jupyter.org/github/sdiehl28/baseball-analytics/blob/master/baseball_jupyter_nb/01_Intro_SQL.ipynb)
  - same as above, but using SQL as much as possible
- [02_Data_Consistency_CSV](https://nbviewer.jupyter.org/github/sdiehl28/baseball-analytics/blob/master/baseball_jupyter_nb/02_Data_Consistency_CSV.ipynb)
  - Compare Retrosheet stats aggregated to season level, to Lahman stats.
  - Compare individual stats aggregated to team level, to team stats, for both Retrosheet and Lahman.
  - Compare batting stats to pitching-allowed stats, for both Retrosheet and Lahman.
- [03a_ParkFactor_CSV](https://nbviewer.jupyter.org/github/sdiehl28/baseball-analytics/blob/master/baseball_jupyter_nb/03a_ParkFactor_CSV.ipynb)
  - Compute the Park Factor, for all teams for several years, accounting for home games not played in home park.
  - Web scrape FanGraphs and compare.
  - It is shown that ESPN and FanGraphs included Boston's runs scored in London, as part of the Fenway Park runs, thereby mistakenly increasing the Park Factor for Fenway Park.
- [03b_ParkFactor_CSV](https://nbviewer.jupyter.org/github/sdiehl28/baseball-analytics/blob/master/baseball_jupyter_nb/03b_ParkFactor_CSV.ipynb)
  - Compute Park Factor, for all teams for several years, accounting for each team's road schedule.
  - It is shown that the road schedule can significantly impact the home park factor for a couple of teams each year.
- [04_LinearWeights_CSV](https://nbviewer.jupyter.org/github/sdiehl28/baseball-analytics/blob/master/baseball_jupyter_nb/04_LinearWeights_CSV.ipynb)
  - Model runs per half-inning using Linear Regression.
  - The coefficient for single, double, triple, home run and other plays is determined.
  - The model accounts for 78% of the variance of runs scored per half-inning.