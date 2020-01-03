# Data Preparation Scripts for Baseball Analytics

All scripts should be run from the download_scripts directory. 

For all scripts:

* --help for help
* -v for verbose: logs to stdout
* --log INFO:  appends to download.log file (at the INFO level)
* --data-dir ../data:   specifies the data directory (default is ../data)

Scripts with example command line arguments:

* **./run_all_scripts.py** --start-year=1974 --end-year=2019
  * convenience script to run all scripts with -v --log=INFO
  * default data directory is ../data
  * all Lahman data is downloaded, but only the years specified for Retrosheet are downloaded
* **./lahman_download.py** -v --log=INFO
  * downloads all the lahman data and unzips it to `../data/lahman/raw`

* **./lahman_wrangle.py** -v -log=INFO
  * converts field names to snake_case
  * performs custom parsing of dates
  * drops fielding columns that have more than 90% missing values
  * optimizes data types
  * persists with optimized data types to `../data/lahman/wrangle`
* **./retrosheet_download.py** -v -log=INFO --start-year=1974 --end-year=2019
  * downloads the retrosheet data and unzips it to `../data/retrosheet/raw`
  * by default, data is downloaded from 1955 through 2019 inclusive
  * this can be changed by using the --start-year and --end-year flags
* **./retrosheet_parse.py** -v --log=INFO --use-datatypes
  * with --use-datatypes option
    * uses the precomputed optimized data type files provided with this repo at `data/retrosheet`
    * this can save several Gigs of RAM, if data goes back to the 1950s or earlier
  * without --use-datatypes option
    * will compute and save the optimized data types
    * may require more than 16 Gig of RAM, if data goes back to the 1950s or earlier
  * runs the cwdaily and cwgame parsers to generate csv files
    * see the "Parsers for Retrosheet" section below
  * all data in the `data/retrosheet/raw` is parsed
  * collects the results into one DataFrame for cwdaily and one DataFrame for cwgame
  * converts the field names to lower case
  * drops columns that have more than 99% missing values
  * persists the results to `../data/retrosheet/collected`
  * the csv files are compressed using gzip
* **./retrosheet_datadictionary.py**
  * this is an optional script which produces the data dictionary for the cwdaily and cwgame parsers
  * the results of running this script are published in this github repo at `data/retrosheet` as cwdaily_datadictionary.txt and cwgame_datadictionary.txt
* **./retrosheet_wrangle.py** -v --log=INFO
  *  data cleanup for non-unique primary key (player_id, game_id)
     *  between 1955 and 2019 there is only one duplicate primary key
  *  custom parsing of game start time
  *  restructure cwdaily output to create batting/pitching/fielding csv files that have a row only if the player has a non-zero batting/pitching/fielding statistic for that game
  *  restructure cwgame output to create stats per team per game (team_game.csv) and stats per game (game.csv)
  *  the csv files are compressed using gzip

#### pytest

After all scripts have run:  pytest -v

WARNING: The data consistency tests, which have tight limits on how different the aggregated Retrosheet data can be from the aggregated Lahman data, were determined using the years 1974 through 2019 inclusive.  These tests may fail if --start-year > 1974 or --end-year < 2019.