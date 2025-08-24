# BookmarkOS Tools

Tools for managing and analyzing bookmarks saved via BookmarkOS.

Just some simple tools (Python, mostly) for converting the backup files from
[Bookmark OS](https://bookmarkos.com/) into data that I can do some basic
stats/analysis on.

The weekly backup file comes in the old bookmarks format used by early-ish
browsers. It is "sort of" HTML, with some tags left without closing
counterparts and attributes on the `A` and `H3` tags that are not standard.
Parsing it was thus a little challenging, since most HTML-parsing packages
either tried to add missing things or just gave up altogether.

## Tools

Tools currently implemented are:

* The Python script `bin/bookmarks2json` parses the backup file line-wise,
  using regular expressions to get the actual content out of the `A` and `H3`
  tags. It produces a JSON file of one object that represents the "root" folder
  of bookmarks.
* The sh/bash script `bin/process_bookmarks` is a simple shell script run as a
  cron-job each Sunday shortly after BookmarkOS pushs the backup file to my
  Dropbox folder. It runs `bookmarks2json` and gzip-compresses the dated copy
  of the backup file and the resulting JSON file.
