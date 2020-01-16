## Retrosheet Parsers

The open source parsers created by Dr. T. L. Turocy to parse the Retrosheet play-by-play data are excellent.   

Retrosheet has 98% of all play-by-play data since 1954 and 100% of all play-by-play data since 1974.  Making use of this data would be very difficult without the parsers.

The data consistency checks in this repo verify that the results of the parsers are consistent with each other.  That is, when the data from different parsers is aggregated to the same level and compared, the results are exactly the same.  Furthermore the parsed Retrosheet data, when aggregated to the season level, is within 1% of the Lahman data for every data consistency test run.

The parsers generate CSV files which can then be wrangled and analyzed.

* cwevent - creates a play-by-play file with a row per play (aka event)
  * about 10 fields were missing from the cwevent output that exist in the cwgame output.  These 10 fields were added by writing code to parse the event_tx field.
  * these 10 new fields were aggregated and compared against cwgame output and found to be identical
* cwdaily - create stats per player per game for batting, fielding and pitching
  * The data wrangling scripts will split the cwdaily output into three files, one each for batting, fielding and pitching
* cwgame - create stats per team per game for batting, fielding and pitching
  * The data wrangling scripts will split the cwgame output into two files, one for team stats per game and one for game stats (e.g. attendance) per game

Parser Description: http://chadwick.sourceforge.net/doc/cwtools.html  
Parser Executables and Source: https://sourceforge.net/projects/chadwick/   

At the time of this writing, version 0.7.2 is the latest version.  Executable versions of the parsers are available for Windows.  Source code is available for Linux and MacOS.

#### Parsed CSV Files

The scripts put the parsed csv files in:  `../data/retrosheet/parsed`.

#### Retrosheet Data Dictionary

The retrosheet_datadictionary.py script will generate a description of the output of the cwdaily and cwgame parsers.

This script has been run and the descriptions have been saved to:  `data/retrosheet/cwdaily_datadictionary.txt` and `data/retrosheet/cwgame_datadictionary.txt`

#### Retrosheet Parsers License

From https://github.com/chadwickbureau/chadwick README

```
This is Chadwick, a library and toolset for baseball play-by-play
and statistics.

Chadwick is Open Source software, distributed under the terms of the 
GNU General Public License (GPL).
```

Parser Description: http://chadwick.sourceforge.net/doc/cwtools.html  
Parser Executables and Source: https://sourceforge.net/projects/chadwick/  

### How to Build Retrosheet Parsers on Linux

If you do not already have a build environment:

1. sudo apt install gcc
2. sudo apt install build-essential

cd to the source directory:

1. ./configure
2. make
3. sudo make install

Result

1. The cw command line tools will be installed in /usr/local/bin.
2. The cw library will be installed in /usr/local/lib.

To allow the command line tools to find the shared libraries, add the following to your .bashrc and then: source .bashrc
`export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib`