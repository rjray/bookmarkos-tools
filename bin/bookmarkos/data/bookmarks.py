"""The data classes used for representing the bookmark data."""

from dataclasses import dataclass, field
import re
from typing import Self


# Regexen for extracting data from a A/H3 tag, and for extracting attributes
EXTRACTION_RE = re.compile(r'^<\w+\s+(.*?)>(.*)</\w+>$')
ATTRIB_RE = re.compile(r'(\w+)="(.*?)"')


type FolderContent = list['Folder | Bookmark']
"""A type-alias for the contents of a folder object, whose elements may be
Bookmarks or other Folder objects."""


@dataclass
class Node():
    """A base-class for Folder and Bookmark."""

    name: str = ''
    "The name given to the Folder or Bookmark"
    created: int = 0
    "The creation time, as UNIX seconds"
    updated: int = 0
    "The last-update time, as UNIX seconds"


@dataclass
class Folder(Node):
    """A simple class for representing a folder."""

    depth: int = 0
    "Depth of this folder in the overall tree"
    content: FolderContent = field(default_factory=list)
    "The contents of this folder"

    def fill(self: Self, markup: str) -> Self:
        """Fill in the Folder object with data from `markup`."""

        if len(markup) > 0:
            text, attrib = parse_fragment(markup)

            self.name = text
            self.created = int(attrib['ADD_DATE'])
            self.updated = int(attrib['LAST_MODIFIED'])

        return self


@dataclass
class Bookmark(Node):
    """A simple class for representing a bookmark."""

    url: str = ''
    "The bookmark's URL"
    visited: int | None = None
    "The last visit-time through the web portal, as UNIX seconds"
    tags: list[str] = field(default_factory=list)
    "Tags for the bookmark"
    notes: str | None = None
    "Notes for the bookmark, if present"

    def fill(self: Self, markup: str) -> Self:
        """Fill in the Bookmark object with data from `markup`."""

        text, attrib = parse_fragment(markup)

        self.name = text
        self.url = attrib['HREF']
        self.created = int(attrib['ADD_DATE'])
        self.updated = int(attrib['LAST_MODIFIED'])
        visited = attrib.get('LAST_VISIT', None)
        if visited is not None:
            self.visited = int(visited)
        self.tags.extend(attrib.get('TAGS', '').split(', '))

        return self


def parse_fragment(content: str) -> tuple[str, dict[str, str]]:
    """Parse the pseudo-HTML data in `content`, returning the text content of
    the tag and a dict of any attributes."""

    # Pull apart `content`. Will result in the attributes as the first match
    # group and the text (that will be used as `name`) as the second group.
    match = EXTRACTION_RE.fullmatch(content)
    if match is None:
        raise ValueError(f'Parse-error on content: {content}')

    attr = match.group(1)
    text = match.group(2)

    # Get all attributes. The `findall` method will return all matches as an
    # iterator.
    attrib: dict[str, str] = {}
    for [key, value] in ATTRIB_RE.findall(attr):
        attrib[key] = value

    return text, attrib
