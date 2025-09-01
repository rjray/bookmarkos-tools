"""Abstraction of the parsing code, for use across multiple tools.

Convert the pseudo-HTML content of a bookmarks backup into a JSON structure
that can be used for other purposes. Because the syntax is not strict HTML it
is parsed with a combination of string-matches and regular expressions with
captures."""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from operator import attrgetter
import re
from typing import TextIO


EXTRACTION_RE = re.compile(r'^<\w+\s+(.*?)>(.*)</\w+>$')
ATTRIB_RE = re.compile(r'(\w+)="(.*?)"')


@dataclass
class Node():
    """A base-class for Folder and Bookmark."""

    name: str = ""
    created: str = ""
    updated: str = ""


@dataclass
class Folder(Node):
    """A simple class for representing a folder."""

    content: list[Node] = field(default_factory=list)

    def fill(self, markup):
        """Fill in the Folder object with data from `markup`."""

        if len(markup) > 0:
            text, attrib = parse_fragment(markup)

            self.name = text
            self.created = datestring(attrib["ADD_DATE"])
            self.updated = datestring(attrib["LAST_MODIFIED"])

        return self


@dataclass
class Bookmark(Node):
    """A simple class for representing a bookmark."""

    url: str = ""
    visited: str = None
    tags: list[str] = field(default_factory=list)

    def fill(self, markup):
        """Fill in the Bookmark object with data from `markup`."""

        text, attrib = parse_fragment(markup)

        self.name = text
        self.url = attrib["HREF"]
        self.created = datestring(attrib["ADD_DATE"])
        self.updated = datestring(attrib["LAST_MODIFIED"])
        self.visited = attrib.get("LAST_VISIT")
        if self.visited is not None:
            self.visited = datestring(self.visited)
        self.tags.extend(attrib.get('TAGS', '').split(', '))

        return self


def parse_fragment(content: str):
    """Parse the pseudo-HTML data in `content`, returning the text content of
    the tag and a dict of any attributes."""
    match = EXTRACTION_RE.fullmatch(content)
    if match is None:
        raise ValueError(f"Parse-error on content: {content}")

    attr = match.group(1)
    text = match.group(2)

    attrib = {}
    for [key, value] in ATTRIB_RE.findall(attr):
        attrib[key] = value

    return text, attrib


def process_dt(line: str, queue: deque, folder: Folder, depth: int) -> None:
    """Process a `<DT>` block."""

    m = re.fullmatch(r'^\s+<DT>(<(A|H3).*>)$', line)
    if m:
        markup = m.group(1)
        tag = m.group(2)

        if tag == "A":
            folder.content.append(Bookmark().fill(markup))
        else:
            next_line = queue.popleft()
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

    m = re.fullmatch(r'^\s+<DD>(.*)$', line)
    notes = m.group(1)

    # Notes go with the most-recent Bookmark
    bookmark = folder.content[-1]
    if isinstance(bookmark, Bookmark):
        bookmark.notes = notes
    else:
        raise ValueError('<DD> tag out of place')


def process_folder(text: str, depth: int, queue: deque) -> Folder:
    """Handle the parsing and conversion of one folder. Called after the
    opening `<DL>` tag has been detected and proceeds until the closing tag
    is detected. Recurses into any sub-folders found."""

    folder = Folder().fill(text)
    padding = '    ' * depth
    end_marker = f"{padding}</DL><p>"
    line = None

    while len(queue) > 0:
        line = queue.popleft()
        if line == end_marker:
            break
        if line == "":
            continue

        if "<DT>" in line:
            process_dt(line, queue, folder, depth)
        elif "<DD>" in line:
            process_dd(line, folder)
        else:
            raise ValueError(f"Unknown content: {line}")

        line = None

    if line is None:
        raise ValueError(f"Closing <DL> for folder {folder.name} not found")

    folder.content.sort(key=attrgetter("name"))
    return folder


def datestring(stamp: str):
    """Turn the given UNIX-style time-stamp `stamp` into a `datetime` object
    in the UTC timezone and converted to ISO8601 format."""
    return datetime.fromtimestamp(int(stamp), tz=timezone.utc).isoformat()


def parse_bookmarks(content: str | TextIO):
    """Process the input in `content` into a `Folder` object that represents
    the full tree."""

    data = []
    if isinstance(content, TextIO):
        data = content.read().split("\n")
    elif content.startswith('<!DOCTYPE'):
        data = content.split("\n")
    else:
        with open(content, encoding="utf8") as ifh:
            data = ifh.read().split("\n")

    # Create a queue, dropping the first 4 lines along the way
    lines = deque(data[4:])
    if lines[0] != "<DL><p>":
        raise ValueError("Missing expected opening <DL>")

    lines.popleft()
    root = process_folder("", 0, lines)

    return root
