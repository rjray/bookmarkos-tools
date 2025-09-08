"""Convert the pseudo-HTML content of a bookmarks backup into a tree structure
that can be used for other purposes. Because the syntax is not strict HTML it
is parsed with a combination of string-matches and regular expressions with
captures."""

from io import TextIOWrapper
from operator import attrgetter
import re
from typing import TextIO

from bookmarkos.data.bookmarks import Bookmark, Folder
from bookmarkos.json_io import read_content


def process_dt(line: str, queue: list[str], folder: Folder, depth: int) -> None:
    """Process a `<DT>` block."""

    # Look for either A or H3 following a DT. Preserve the specific tag and the
    # markup itself.
    m = re.fullmatch(r'^\s+<DT>(<(A|H3).*>)$', line)
    if m:
        markup = m.group(1)
        tag = m.group(2)

        if tag == 'A':
            # Bookmark. Simple.
            folder.content.append(Bookmark().fill(markup))
        else:
            # Folder. First we have to ensure that the next line is the opening
            # of a folder, then we process it recursively.
            next_line = queue.pop(0)
            if re.fullmatch(r'^\s+<DL><p>$', next_line):
                folder.content.append(
                    process_folder(markup, depth + 1, queue)
                )
            else:
                raise ValueError(
                    f"Missing opening <DL> after '{markup}'"
                )
    else:
        raise ValueError(f"Unrecognized line: '{line}'")


def process_dd(line: str, folder: Folder) -> None:
    """Process a `<DD>` tag that follows a bookmark declaration."""

    notes = None
    # This RE only looks for all content following the DD, to the end of the
    # line.
    m = re.fullmatch(r'^\s+<DD>(.*)$', line)
    if m:
        notes = m.group(1)

    # Notes go with the most-recent entity, which must be a `Bookmark`.
    bookmark = folder.content[-1]
    if isinstance(bookmark, Bookmark) and notes:
        bookmark.notes = notes
    else:
        raise ValueError('<DD> tag out of place')


def process_folder(text: str, depth: int, queue: list[str]) -> Folder:
    """Handle the parsing and conversion of one folder. Called after the
    opening `<DL>` tag has been detected and proceeds until the closing tag
    is detected. Recurses into any sub-folders found."""

    # Start with a fresh `Folder` instance, filled in with the content passed
    # as `text`. The `depth` parameter is used to create the marker we will
    # look for as signaling the end of the folder.
    folder = Folder().fill(text)
    padding = '    ' * depth
    end_marker = f'{padding}</DL><p>'
    line = None

    while len(queue) > 0:
        line = queue.pop(0)
        if line == end_marker:
            break
        # There shouldn't be any blank lines, but protect against it to be sure
        if not line:
            continue

        # Within the opening DL and the value of `end_marker`, we should only
        # see DT and DD tags.
        if '<DT>' in line:
            process_dt(line, queue, folder, depth)
        elif '<DD>' in line:
            process_dd(line, folder)
        else:
            raise ValueError(f'Unknown content: {line}')

        line = None

    # This means we ran out of lines before closing the folder.
    if line is None:
        raise ValueError(f'Closing <DL> for folder {folder.name} not found')

    # Sorting by name isn't really necessary, but it makes the data easier to
    # test/triage.
    folder.content.sort(key=attrgetter('name'))
    return folder


def parse_bookmarks(content: str | TextIO | TextIOWrapper) -> Folder:
    """Process the input in `content` into a `Folder` object that represents
    the full tree."""

    data = []
    # Three types of value for `content` are accepted: an open FH, a string
    # that starts with a DOCTYPE declaration, or a string that represents a
    # file name.
    if isinstance(content, (TextIO, TextIOWrapper)):
        data = content.read().split("\n")
    elif content.startswith('<!DOCTYPE'):
        data = content.split("\n")
    else:
        data = read_content(content).split("\n")

    # Drop the first 4 lines of content, not used for anything.
    lines = data[4:]
    if lines[0] != '<DL><p>':
        raise ValueError('Missing expected opening <DL>')

    lines.pop(0)

    return process_folder('', 0, lines)
