"""Convert the pseudo-HTML content of a bookmarks backup into a tree structure
that can be used for other purposes. Because the syntax is not strict HTML it
is parsed with a combination of string-matches and regular expressions with
captures."""

from operator import attrgetter
import re
from typing import TextIO

from .data.bookmarks import Bookmark, Folder


EXTRACTION_RE = re.compile(r'^<\w+\s+(.*?)>(.*)</\w+>$')
ATTRIB_RE = re.compile(r'(\w+)="(.*?)"')


def process_dt(line: str, queue: list[str], folder: Folder, depth: int) -> None:
    """Process a `<DT>` block."""

    m = re.fullmatch(r'^\s+<DT>(<(A|H3).*>)$', line)
    if m:
        markup = m.group(1)
        tag = m.group(2)

        if tag == 'A':
            folder.content.append(Bookmark().fill(markup))
        else:
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
    m = re.fullmatch(r'^\s+<DD>(.*)$', line)
    if m:
        notes = m.group(1)

    # Notes go with the most-recent Bookmark
    bookmark = folder.content[-1]
    if isinstance(bookmark, Bookmark) and notes:
        bookmark.notes = notes
    else:
        raise ValueError('<DD> tag out of place')


def process_folder(text: str, depth: int, queue: list[str]) -> Folder:
    """Handle the parsing and conversion of one folder. Called after the
    opening `<DL>` tag has been detected and proceeds until the closing tag
    is detected. Recurses into any sub-folders found."""

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

        if '<DT>' in line:
            process_dt(line, queue, folder, depth)
        elif '<DD>' in line:
            process_dd(line, folder)
        else:
            raise ValueError(f'Unknown content: {line}')

        line = None

    if line is None:
        raise ValueError(f'Closing <DL> for folder {folder.name} not found')

    folder.content.sort(key=attrgetter('name'))
    return folder


def parse_bookmarks(content: str | TextIO) -> Folder:
    """Process the input in `content` into a `Folder` object that represents
    the full tree."""

    data = []
    if isinstance(content, TextIO):
        data = content.read().split("\n")
    elif content.startswith('<!DOCTYPE'):
        data = content.split("\n")
    else:
        with open(content, encoding='utf8') as ifh:
            data = ifh.read().split("\n")

    # Create a queue, dropping the first 4 lines along the way
    lines = data[4:]
    if lines[0] != '<DL><p>':
        raise ValueError('Missing expected opening <DL>')

    lines.pop(0)

    return process_folder('', 0, lines)
