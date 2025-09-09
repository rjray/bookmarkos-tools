# BookmarkOS Tools

Tools for managing and analyzing bookmarks saved via BookmarkOS.

Just some simple tools (Python, mostly) for converting the backup files from
[Bookmark OS](https://bookmarkos.com/) into data that I can do some basic
metrics/analysis on.

The weekly backup file comes in the old bookmarks format used by early-ish
browsers. It is "sort of" HTML, with some tags left without closing
counterparts and attributes on the `A` and `H3` tags that are not standard.
Parsing it was thus a little challenging, since most HTML-parsing packages
either tried to add missing things or just gave up altogether.

_**Caveat**: While I am a seasoned programmer, I'm still fairly new to Python.
There are almost certainly going to be things in here that could have been done
better._

## Tools

Tools currently implemented are:

- The Python script `bin/bookmarks2json` parses the backup file line-wise,
  using regular expressions to get the actual content out of the `A` and `H3`
  tags. It produces a JSON file of one object that represents the "root" folder
  of bookmarks.
- The Python script `bin/bookmarks_report` takes one or two JSON files produced
  by `bookmarks2json` and produces reports. Right now, it only does a limited
  text-only report on weekly activity.
- The Python script `bin/restore_bookmarks` takes a JSON file (presumably the
  oldest you have) and works backwards to rebuild JSON files for each week that
  represent what you would have gotten in that week's backup. There are some
  corner cases it can't detect, but the data should be close to 99.5% or so.
- The sh/bash script `bin/process_bookmarks` is a simple shell script run as a
  cron-job each Sunday shortly after BookmarkOS pushs the backup file to my
  Dropbox directory. It runs `bookmarks2json` and gzip-compresses the dated
  copy of the backup file and the resulting JSON file.

## Libraries

As this has grown, some code has been refactored out into separate library
files, both for sharing across tools and to keep things clean and readable.
These are all in the `bookmarkos` directory (and sub-directories), and the
files are:

- `json_io.py`: Functions to read and write the JSON content. Reading content
  looks to the file name to determine if it is compressed or not and reads it
  accordingly. Writing content also uses the file name (unless the `file`
  argument is an existing open filehandle) to decide whether to write compressed
  data. The `write_json_data` function also takes arguments that can be passed
  to the Gzip compression and the JSON encoding. The `read_plain_json` function
  reads and decodes JSON data into a structure of Python `dict` objects. The
  `read_bookmarks_json` function reads and decodes the JSON, but reinstantiates
  it as `Folder` and `Bookmark` objects.
- `metrics.py`: Encapsulation of the logic used to calculate all the metrics
  gathered on bookmarks data.
- `parser.py`: Encapsulation of the parsing logic used to take a bookmarks file
  and generate the corresponding tree of Python objects that can then be
  serialized as JSON.
- `data`: This is a sub-directory for the modules that provide data classes.
  - `bookmarks.py`: The data classes for bookmark representation (`Bookmark`
    and `Folder`)
  - `metrics.py`: The data classes for the metrics that are gathered
    (`Metrics`, `BookmarksMetrics`, `FoldersMetrics`, `TagsMetrics`).

## Notes On File Structure, Data Structures, and Parsing

This section will gather notes on the general parsing itself, specifically the
structure of the file, the data structures used for internal representation,
and the parsing process.

### File structure

As mentioned above, the format of the `backup.html` file that BookmarkOS creates
is an abbreviated form of HTML as was used early on in browsers for storing and
exporting bookmarks:

<!-- prettier-ignore -->
```html
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><A HREF="https://github.com/ahembree/ansible-hms-docker"
                ADD_DATE="1641921698"
                LAST_VISIT="1648322750"
                LAST_MODIFIED="1755453381"
                TAGS="plex, github, ansible, docker">
            ahembree/ansible-hms-docker: Ansible playbook for automated home media server setup
        </A>
    <DT><H3 ADD_DATE="1534112986" LAST_MODIFIED="1563985394">Apple</H3>
```

(Line breaks and extra indentation were added to the `<A>` tag for readability.
In the file, all such tags are on a single line along with the leading `<DT>`.)

This shows the preamble (the first four lines), the start of the top-level
("root") folder, a bookmark in the root folder and the start of a sub-folder
("Apple"). There are three time-stamps, one of which (`LAST_VISIT`) is only
present on bookmarks. All time-stamps are UNIX/Linux format and represent the
number of seconds since the epoch (January 1, 1970, midnight, UTC). The `TAGS`
attribute is the list of tags with each separated by a comma and a single space.
Tags themselves may contain spaces, but not commas (the form used to register a
bookmark interprets a comma character as the separator when entering tags).

### Data structures

To represent the data internally, a small hierarchy of three classes were used.
These were defined using the `dataclasses` Python module, as none of them
needed to define any extensive amount of functionality.

The classes are defined in the `bookmarkos/parser.py` module, and are:

- **Node**: This is the base-class, and it defines the properties `name`
  (string), `created` (integer), and `updated` (integer).
- **Bookmark**: This class extends `Node` to represent a bookmark. It adds the
  properties `url` (string), `visited` (integer that may be null), `notes`
  (string), and `tags` (a list of strings).
- **Folder**: This class extends `Node` to represent a folder. It adds the
  property `content`, which is a list of objects that derive from `Node`
  (`Bookmark` or `Folder` instances).

There is nothing really special about these three. The two concrete classes
each define a `fill` method that takes a string representing the markup from
the input file that is specific to the class (the `<A>` or `<H3>` tags). The
markup is parsed with regular expressions and the attributes of the object are
filled in.

### Parsing notes

Parsing was done along the following rules. Most sample strings in the context
of parsing will be regular expression syntax.

1. The first four lines are always discarded
2. The first "relevant" line will match the sequence, `^<DL><p>`. This
   represents the "root" folder which has no name or time-stamp attributes.
3. A sequence of `\s*<DL><p>` starts a folder. The amount of leading whitespace
   determines the "depth" of the folder.
4. A sequence of `\s*</DL><p>` closes a folder. The amount of leading whitespace
   should match the opening tag.
5. A sequence of `\s*<DT><A .*?>.*</A>` defines a bookmark in the current
   folder.
6. A sequence of `\s*<DT><H3 .*?>.*</H3>` provides the name of a folder, and
   must _always_ be immediately followed by the sequence from rule 2.
7. A sequence of `\s*<DD>.*` defines the notes for a bookmark and must _always_
   immediately follow the sequence from rule 4.
8. The last line of the file will match the sequence, `^</DL><p>`. Note that
   there is no leading space on this line.
9. The bookmarks backup file is UTF-8 encoded. It must be read in this encoding
   and the resulting JSON should be likewise encoded.

The logic used to parse is line-wise and primarily uses regular expressions. It
is somewhat "hacky", but has far less overhead than trying to coerce the data
into something that Python's `html.parser` can work with.
