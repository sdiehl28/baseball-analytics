# Data Preparation Scripts for Baseball Analytics

These scripts download, parse and wrangle the Lahman and Retrosheet data.

An optional script creates Postgres tables with appropriate primary key constraints and loads the csv files into these tables.

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
  * all data is downloaded but only the years specified are parsed and wrangled
* **./lahman_download.py** -v --log=INFO
  * downloads all the lahman data and unzips it to `../data/lahman/raw`

* **./lahman_wrangle.py** -v -log=INFO
  * converts field names to snake_case
  * performs custom parsing of dates
  * drops fielding columns that have more than 90% missing values
  * optimizes data types
  * persists with optimized data types to `../data/lahman/wrangle`
* **./retrosheet_download.py** -v -log=INFO
  * downloads the retrosheet data and unzips it to `../data/retrosheet/raw`
* **./retrosheet_parse.py** -v --log=INFO --start-year=1974 --end-year=2019
  * parses data in `data/retrosheet/raw` for the specified years
    * cwdaily and cwgame are always run
    * use '--run-cwevent' to run the cwevent parser as well
    * use '--cwevent-fields' to specify your own set of fields using the cwevent syntax
      * for example, to specify all fields use: --cwevent-fields='-f 0-96 -x 0-62'
* **./retrosheet_collect.py** -v --log=INFO --use-datatypes
  * with --use-datatypes option
    * uses the precomputed optimized data types: `data/retrosheet/*_types.csv`
    * this can save several Gigs of RAM, if data goes back to the 1950s or earlier
  * without --use-datatypes option
    * will compute and save the optimized data types
    * may require more than 16 Gig of RAM, if data goes back to the 1950s or earlier
  * collects the results into one DataFrame for cwdaily and one DataFrame for cwgame
    * if there are cwevent files, it will collect these into a single DataFrame as well
    * if there are cwevent files, it will add the following new fields to make play-by-play analysis easier: so, sb, cs, bk, bb, ibb, hbp, xi, single, double, triple, hr
  * converts the field names to lower case
  * drops columns that have more than 99% missing values
  * persists the results to `../data/retrosheet/collected`
  * the csv files are compressed using gzip
* **./retrosheet_datadictionary.py**
  * this is an optional script which produces the data dictionary for the cwdaily and cwgame parsers
  * the results of running this script are published in this github repo at `data/retrosheet` as cwdaily_datadictionary.txt and cwgame_datadictionary.txt
* **./retrosheet_wrangle.py** -v --log=INFO
  *  data cleanup for non-unique primary key (player_id, game_id)
     *  between 1948 and 2019 there is only one duplicate primary key
  *  custom parsing of game start time
  *  restructure cwdaily output to create batting/pitching/fielding csv files that have a row only if the player has a non-zero batting/pitching/fielding statistic for that game
  *  restructure cwgame output to create stats per team per game (team_game.csv) and stats per game (game.csv)
  *  the csv files are compressed using gzip
* **./postgres_load_data.py** -v --log=INFO
  *  optional script to:
     *  create tables with optimized data types
     *  create primary and foreign key constraints
     *  load data into tables
  *  the baseball database must have already been created
     *  connect string:  f'postgresql://{db_user}:{db_pass}@localhost:5432/baseball' 

### Performing Data Validation

pytest is used to automate the running of more than 50 data integrity and data consistency tests.

Running pytest:

* recommend: 'pytest -v'
* must be run from the `download_scripts` directory
* must be run after the scripts which download and parse the data have been run
* accepts custom option: --data-dir=<data_directory>

If you like, you may spot check the data using [Baseball Reference](https://www.baseball-reference.com/).  Baseball Reference uses the Retrosheet data.  The box score for a game can be constructed from the game_id using:  
 `'https://www.baseball-reference.com/boxes/' + game_id.str[:3] + '/' + game_id + '.shtml'`  
 For example, to verify that there are two entries for Chris Young for game_id = BOS201708250, the url is:  
https://www.baseball-reference.com/boxes/BOS/BOS201708250.shtml

### Rerunning the Scripts

It is rarely necessary to re-download the data.  Minor tweaks are continually being made to Lahman and Retrosheet for very old data, but recent data is usually accurate and complete the first time it is made available.

The data is not updated during the season.  It is added to both Lahman and Retrosheet around late December.  For example, all of the 2019 regular and post-season data for both Lahman and Retrosheet became available in late December 2019.

To rerun the scripts, it is only necessary to remove the data from data directories other than the raw data directories.