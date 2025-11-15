# TODO List

Ideas and goals that haven't been implemented yet.

## General

1. Implement a database layer for data
   1. Use native SQLite bindings
   2. Schema
   3. Initialization code
2. Decide on whether to go database-only or support files as well
3. Turn `restore_bookmarks` into an initialization tool that takes all existing
   backup files and creates either the DB or (and?) files for all weeks
4. Determine the option-needs of each tool and set up the TOML file
5. Add support for the TOML file alongside existing options-handling
6. Move processing and storage out of the `Bookmark OS` Dropbox directory

## Parsing

1. Fix parser code to no longer strip folder-related lines before processing
2. ~~Make `bookmarks2json` default to reading from/writing to compressed files~~
3. Database support

## Metrics

1. Implement remaining items from [METRICS.md](METRICS.md)
2. Database support
3. Preservation of calculated metrics
4. Calculation of other gaps
   1. Do this proactively or only create/save on-demand?
   2. Keep this in mind when designing the DB schema

## Reporting

1. Direct emailing support
2. Database support
3. Get weekly report into HTML and into direct emailing, first
4. Determine the planned report types
   1. Weekly
   2. Monthly
   3. Full data (what would that be?)
   4. Trends (very much open to interpretation)
5. Abstract all (planned) report types
   1. Plain text
   2. HTML
   3. Others?

## Visualization

For vizualization, a basic SPA will be written. Some initial ideas:

- Will require the database
- Growth of bookmarks over time
- Additions by day-of-the-week
- Tag cloud
  - Searching for entries
  - Showing related tags
  - Changes to the cloud over time
- Display of trends

More to come on this later.
