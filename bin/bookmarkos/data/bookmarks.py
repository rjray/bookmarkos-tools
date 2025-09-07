"""The data classes used for representing the bookmark data."""

from dataclasses import dataclass, field
import re
from typing import Self


EXTRACTION_RE = re.compile(r'^<\w+\s+(.*?)>(.*)</\w+>$')
ATTRIB_RE = re.compile(r'(\w+)="(.*?)"')


@dataclass
class Node():
    """A base-class for Folder and Bookmark."""

    name: str = ''
    created: int = 0
    updated: int = 0


@dataclass
class Folder(Node):
    """A simple class for representing a folder."""

    content: list[Node] = field(default_factory=list)

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
    visited: int | None = None
    tags: list[str] = field(default_factory=list)
    notes: str | None = None

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
    match = EXTRACTION_RE.fullmatch(content)
    if match is None:
        raise ValueError(f'Parse-error on content: {content}')

    attr = match.group(1)
    text = match.group(2)

    attrib: dict[str, str] = {}
    for [key, value] in ATTRIB_RE.findall(attr):
        attrib[key] = value

    return text, attrib
