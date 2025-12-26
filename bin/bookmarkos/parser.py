"""Convert the pseudo-HTML content of a bookmarks backup into a tree structure
that can be used for other purposes. Because the syntax is not strict HTML it
is parsed with a combination of string-matches and regular expressions with
captures."""

from collections import deque
from io import StringIO, TextIOWrapper
from operator import attrgetter
import re
from typing import TextIO

from bookmarkos.data.bookmarks import Bookmark, Folder
from bookmarkos.json_io import read_content

# Pre-compiled regex patterns for performance
DT_PATTERN = re.compile(r'^\s+<DT>(<(A|H3) .*>)$')
DL_OPEN_PATTERN = re.compile(r'^\s+<DL><p>$')
DD_PATTERN = re.compile(r'^\s+<DD>(.*)$')

# Constants
HEADER_LINES = 4
ROOT_DL_TAG = '<DL><p>'
MAX_NESTING_DEPTH = 100


def process_dt(
        line: str,
        queue: deque[str],
        folder: Folder,
        parent: list[str],
        line_number: int = 0
) -> None:
    """Process a `<DT>` block."""

    # Add recursion depth protection
    if len(parent) > MAX_NESTING_DEPTH:
        raise ValueError(
            f"Maximum nesting depth exceeded at line {line_number}")

    # Look for either A or H3 following a DT. Preserve the specific tag and the
    # markup itself.
    m = DT_PATTERN.fullmatch(line)
    if m:
        markup = m.group(1)
        tag = m.group(2)

        if tag == 'A':
            # Bookmark. Simple.
            bookmark = Bookmark().fill(markup)
            bookmark.parent = parent.copy()
            folder.content.append(bookmark)
        elif tag == 'H3':
            # Folder. First we have to ensure that the next line is the opening
            # of a folder, then we process it recursively.
            if not queue:
                raise ValueError(
                    f"Unexpected end of input after folder '{markup}'" +
                    f" at line {line_number}"
                )

            next_line = queue.popleft()
            if DL_OPEN_PATTERN.fullmatch(next_line):
                subfolder = process_folder(
                    markup, queue, parent, line_number + 1
                )
                folder.content.append(subfolder)
            else:
                # Better error recovery - put line back
                queue.appendleft(next_line)
                raise ValueError(
                    f"Missing opening <DL> after '{markup}' at line" +
                    f" {line_number}, found '{next_line}'"
                )
        else:
            raise ValueError(
                f"Unknown tag type '{tag}' in <DT> at line {line_number}")
    else:
        raise ValueError(
            f"Unrecognized <DT> format at line {line_number}: '{line}'")


def process_dd(line: str, folder: Folder, line_number: int = 0) -> None:
    """Process a `<DD>` tag that follows a bookmark declaration."""

    # Check if folder has any content
    if not folder.content:
        raise ValueError(
            f'<DD> tag found but no previous bookmark at line {line_number}')

    notes = None
    # This RE only looks for all content following the DD, to the end of the
    # line.
    m = DD_PATTERN.fullmatch(line)
    if m:
        notes = m.group(1)
    else:
        raise ValueError(f'Malformed <DD> tag at line {line_number}: "{line}"')

    # Notes go with the most-recent entity, which must be a `Bookmark`.
    last_item = folder.content[-1]
    if isinstance(last_item, Bookmark):
        if notes:  # Only set if notes exist
            last_item.notes = notes
    else:
        raise ValueError(
            f'<DD> tag found after non-bookmark item at line {line_number}'
        )


def process_folder(
        text: str,
        queue: deque[str],
        path: list[str],
        line_number: int = 0
) -> Folder:
    """Handle the parsing and conversion of one folder. Called after the
    opening `<DL>` tag has been detected and proceeds until the closing tag
    is detected. Recurses into any sub-folders found."""

    depth = len(path)
    # Add recursion depth protection
    if len(path) > MAX_NESTING_DEPTH:
        raise ValueError(
            f"Maximum folder nesting depth exceeded at line {line_number}"
        )

    # Start with a fresh `Folder` instance, filled in with the content passed
    # as `text`. The `depth` parameter is used to create the marker we will
    # look for as signaling the end of the folder.
    folder = Folder().fill(text)
    folder.depth = depth
    folder.parent = path.copy()
    padding = '    ' * depth
    end_marker = f'{padding}</DL><p>'
    parent = path + [folder.name]

    current_line_number = line_number
    line = None

    while queue:
        current_line_number += 1
        line = queue.popleft()

        if line == end_marker:
            break

        # Log empty lines for debugging but continue
        if not line:
            # Could add logging here instead of silent skip
            continue

        # Within the opening DL and the value of `end_marker`, we should only
        # see DT and DD tags.
        try:
            if '<DT>' in line:
                process_dt(line, queue, folder, parent, current_line_number)
            elif '<DD>' in line:
                process_dd(line, folder, current_line_number)
            else:
                raise ValueError(
                    f'Unknown content at line {current_line_number}: {line}')
        except ValueError as e:
            # Add context to errors
            raise ValueError(
                f'Error processing "{folder.name}" at depth {len(parent)}: {e}'
            ) from e

        line = None

    # This means we ran out of lines before closing the folder.
    if line is None:
        raise ValueError(
            f'Closing <DL> for folder "{folder.name}" not found'
        )

    # Sorting by name isn't really necessary, but it makes the data easier to
    # test/triage.
    folder.content.sort(key=attrgetter('name'))
    return folder


def parse_bookmarks(content: str | TextIO | TextIOWrapper | StringIO) -> Folder:
    """Process the input in `content` into a `Folder` object that represents
    the full tree."""

    data = []
    # Three types of value for `content` are accepted: an open FH, a string
    # that starts with a DOCTYPE declaration, or a string that represents a
    # file name.
    if isinstance(content, (TextIO, TextIOWrapper, StringIO)):
        data = content.read().split("\n")
    elif isinstance(content, str) and content.startswith('<!DOCTYPE'):
        data = content.split("\n")
    else:
        data = read_content(content).split("\n")

    # Validate minimum content length
    if len(data) < HEADER_LINES + 1:
        raise ValueError(
            f'Expected at least {HEADER_LINES + 1} lines, got {len(data)}')

    # Drop the first 4 lines of content, not used for anything.
    lines = data[HEADER_LINES:]
    if not lines or lines[0] != ROOT_DL_TAG:
        actual = lines[0] if lines else "EOF"
        raise ValueError(f'Missing expected opening <DL>, found: "{actual}"')

    lines.pop(0)

    # Convert to deque for efficient operations
    line_queue = deque(lines)

    return process_folder('', line_queue, [], HEADER_LINES + 1)
