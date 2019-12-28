# Download Scripts for Baseball Analytics

&#x1F534; Under Construction - may be ready for use by 12/31/19  

Scripts are provided to:

- download
- parse
- tidy
- validate and clean

Major League Baseball (MLB) data in preparation for easy analysis with Pandas or SQL.

The end result will be a set of csv files, with data types per column in associated csv files, which can be loaded into Pandas or any database.

## Script 

cd to the download_scripts directory.  All scripts have help.   Scripts can be run as:

* `python lahman_download.py --help` or 
* `lahman_download.py --help` if the script has execute permission.

After the scripts have been run, pytest can be run to verify that the download succeeded and the data is fine.

For all scripts:

* -v for verbose: logs to stdout
* --log INFO:  appends to download.log file (at the INFO level)
* --data-dir ../data:   specifies the data directory (default is ../data)

Scripts with example command line arguments:

* **run_all_scripts.py** --data-dir=../data
  * convenience script to run all scripts with -v --log=INFO for the data directory specified
* **lahman_download.py** -v --log=INFO --data-dir=../data
  * downloads all the lahman data and unzips it to `../data/lahman/raw`

* **lahman_wrangle.py** -v -log=INFO --data-dir=../data
  * converts field names to snake_case
  * performs custom parsing of dates
  * drops fielding columns that have more than 90% missing values
  * optimizes data types
  * persists with optimized data types to `../data/lahman/wrangle`
* **retrosheet_download.py** -v -log=INFO --data-dir=../data
  * downloads the retrosheet data and unzips it to `../data/retrosheet/raw`
  * by default, data is downloaded from 1955 through 2019 inclusive
  * this can be changed by using the --start-year and --end-year flags
* **retrosheet_parse.py** -v --log=INFO --data-type --data-dir=../data
  * with --data-type option
    * uses the precomputed optimized data type files provided with this repo at `data/retrosheet`
    * this can save several Gigs of RAM, if data goes back to the 1950s or earlier
  * without --data-type option
    * will compute the optimized data types
    * may require more than 16 Gig of RAM, if data goes back to the 1950s or earlier
  * runs the cwdaily and cwgame parsers to generate csv files
    * see the "Parsers for Retrosheet" section below
  * all data in the `data/retrosheet/raw` is parsed
  * collects the results into one DataFrame for cwdaily and one DataFrame for cwgame
  * optimizes all data types
  * converts the field names to lower case
  * drops columns that have more than 95% missing values
  * persists the results to `../data/retrosheet/collected`
  * the DataFrames are compressed using gzip
    * the compression ratio is about 18:1
* **retrosheet_datadictionary.py**
  * this is an optional script which produces the data dictionary for the generated csv files
  * script results are saved in `data/retrosheet` directory and are published in this github repo
* **retrosheet_wrangle.py** -v --log=INFO --data-type --data-dir=../data
  *  custom parsing of game time
  *  data cleanup for non-unique (player_id, game_id) records
  *  and much more ...
* **tests/test_data.py**
  * after running the above scripts, run 'pytest' from the same directory
  * pytest relies on
    * conftest.py and pytest.ini in the download_scripts directory
    * tests/test_data.py