## Retrosheet Parsers: Source and Exectuables

The open source parsers created by Dr. T. L. Turocy to parse the Retrosheet play-by-play data are excellent. 

These parsers must be installed and on the path for the Python scripts to make use of them.

Parser Description: http://chadwick.sourceforge.net/doc/cwtools.html  
Parser Executables and Source: https://sourceforge.net/projects/chadwick/   

At the time of this writing, version 0.7.2 is the latest version.  Executable versions of the parsers are available for Windows.  Source code is available for Linux and MacOS.  See [How to Build Retrosheet Parsers on Linux](#how-to-build-retrosheet-parsers-on-linux)

## Retrosheet Parsers

Three parsers are used:

* cwevent - creates one record for each single, double, error, stolen base, hit by pitch, balk, etc.
* cwdaily - similar to a box score in which each players stats for a game are created
* cwgame - similar to a line score in which each teams stats for a game are created

In more detail:

* cwevent
  * was missing about 10 fields that cwgame creates and are useful for analysis.  These 10 fields were added by using regular expressions to parse the event_tx field.  These 10 fields were then aggregated to the game level and verified to be 100% consistent with the output of cwgame.
* cwdaily
  * the output of cwdaily is split into 3 csv files: batting, pitching and fielding.  This is how Lahman structures their data as well.
* cwgame
  * the output of cwgame is split into 2 csv files: team_game and game.  The data in game is data specific to a game such as which park it was played in.  The data in team_game is specific to a team for that game.

All possible fields are extracted from the cwdaily and cwgame parsers.  Both parsers are run automatically by the retrosheet_parse.py script. 

The cwevent parsers creates a great many rows.  As such a default subset of the fields is selected.  This parser is optionally run by the retrosheet_parse.py script.

## Retrosheet Parsers License

From https://github.com/chadwickbureau/chadwick README

```
This is Chadwick, a library and toolset for baseball play-by-play
and statistics.

Chadwick is Open Source software, distributed under the terms of the 
GNU General Public License (GPL).
```

Parser Description: http://chadwick.sourceforge.net/doc/cwtools.html  
Parser Executables and Source: https://sourceforge.net/projects/chadwick/  

## How to Build Retrosheet Parsers on Linux

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