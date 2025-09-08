"""Abstract all the input/output of JSON data for the suite of tools."""

import gzip as GZ
from io import TextIOWrapper
import json as JS
from typing import Any, Self, TextIO

from bookmarkos.data.bookmarks import Folder, Bookmark


class BasicEncoder(JS.JSONEncoder):
    """A wrapper-style class around `JSONEncoder` to handle dict-based objects
    in the structure being converted to JSON. Also catches `set` instances and
    converts them to sorted lists."""

    def default(self, o):
        if isinstance(o, set):
            return sorted(list(o))

        return o.__dict__


class BookmarksDecoder(JS.JSONDecoder):
    """A JSON decoder class for turning bookmarks JSON back into a tree
    structure of `Folder` and `Bookmark` instances."""

    def __init__(self: Self, *args, **kwargs):
        super().__init__(object_hook=self.object_transform, *args, **kwargs)

    def object_transform(self: Self, obj: dict[str, Any]):
        """Handle the turning of vanilla objects into either `Folder` or
        `Bookmark` instances. Rather than encode a special dictionary
        property into the JSON, this version looks for attributes that
        uniquely discern the two types."""

        if 'tags' in obj:
            return Bookmark(**obj)

        if 'content' in obj:
            return Folder(**obj)

        return obj


def read_content(file: str | TextIO | TextIOWrapper) -> str:
    """Read the content of `file`, regardless of its type (including if the
    file name indicates compressed data)."""

    if isinstance(file, (TextIO, TextIOWrapper)):
        fh = file
    elif file.endswith('.gz'):
        # Gzip'd content
        fh = GZ.open(file, 'rt')
    else:
        # Assume plain-text content
        fh = open(file, 'r', encoding='utf8')

    with fh:
        content = fh.read()

    return content


def read_plain_json(file: str | TextIO | TextIOWrapper) -> Any:
    """Read the JSON content from the given file. Handles gzip-compressed
    content. Returns vanilla JSON."""

    return JS.loads(read_content(file))


def read_bookmarks_json(file: str | TextIO | TextIOWrapper) -> Folder:
    """Read the JSON version of bookmarks data from the given input source and
    restore it to a tree structure based on the `Folder` and `Bookmark`
    classes."""

    return JS.loads(read_content(file), cls=BookmarksDecoder)


def write_json_data(
    data: Any, file: str | TextIO | TextIOWrapper, *,
    json: dict[str, Any] | None = None, gzip: dict[str, Any] | None = None
) -> None:
    """Write the given data as JSON content. Handles gzip-compressing of
    content."""

    json_args: dict[str, Any] = {
        'cls': BasicEncoder,
        'ensure_ascii': False,
    }
    if json is not None:
        json_args |= json
    gzip_args: dict[str, Any] = {
        'compresslevel': 9,
    }
    if gzip is not None:
        gzip_args |= gzip

    if isinstance(file, (TextIO, TextIOWrapper)):
        fh = file
    elif file.endswith('.gz'):
        # Gzip'd output
        fh = GZ.open(file, 'wt', **gzip_args)
    else:
        # Assume plain-text output
        fh = open(file, 'w', encoding='utf8')

    with fh:
        JS.dump(data, fh, **json_args)
