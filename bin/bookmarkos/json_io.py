"""Abstract all the input/output of JSON data for the suite of tools."""

import gzip as GZ
from io import StringIO, TextIOWrapper
import json as JS
from typing import Any, Self, TextIO

from bookmarkos.data.bookmarks import Folder, Bookmark


type ReadableSource = str | TextIO | TextIOWrapper | StringIO
"""Type alias for any source that can be read as text, including file names and
file-like objects."""

type WritableSource = str | TextIO | TextIOWrapper | StringIO
"""Type alias for any destination that can be written as text, including file
names and file-like objects."""


class BasicEncoder(JS.JSONEncoder):
    """A wrapper-style class around `JSONEncoder` to handle dict-based objects
    in the structure being converted to JSON. Also catches `set` instances and
    converts them to sorted lists."""

    def default(self, o):
        """Default handler for anything that is an object."""

        if isinstance(o, set):
            # A `Set` is encoded as a sorted list of the contents
            return sorted(o)

        # All other objects return their `dict` representation.
        return o.__dict__


class BookmarksDecoder(JS.JSONDecoder):
    """A JSON decoder class for turning bookmarks JSON back into a tree
    structure of `Folder` and `Bookmark` instances."""

    def __init__(self: Self, *args, **kwargs):
        """Object constructor. Call the superclass initialization with all
        arguments passed here, as well as a keyword argument setting up a hook
        for decoding objects."""
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


def read_content(file: ReadableSource) -> str:
    """Read the content of `file`, regardless of its type (including if the
    file name indicates compressed data).

    Args:
        file: A file path (string) or an open file-like object

    Returns:
        The content of the file as a string

    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If permission is denied to read the file
        OSError: If other I/O errors occur
        ValueError: If file parameter is not a valid type
    """

    if isinstance(file, (TextIO, TextIOWrapper, StringIO)):
        # A pre-existing file-handle. It will be read from directly and we
        # return immediately (without closing the existing handle).
        return file.read()

    # Input validation for string file paths
    if not isinstance(file, str):
        raise ValueError(
            "File parameter must be a string path or file-like object"
        )

    if not file.strip():
        raise ValueError("File path cannot be empty or whitespace")

    # Case-insensitive compression detection
    is_compressed = file.lower().endswith('.gz')

    try:
        if is_compressed:
            # Gzip'd content - create file handle directly in context manager
            with GZ.open(file, 'rt') as fh:
                content = fh.read()
        else:
            # Assume plain-text content - create file handle directly
            with open(file, 'r', encoding='utf8') as fh:
                content = fh.read()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"The file '{file}' was not found") from exc
    except PermissionError as exc:
        raise PermissionError(
            f"Permission denied when trying to read '{file}'") from exc
    except OSError as e:
        raise OSError(f"I/O error when reading '{file}': {e}") from e

    return content


def read_plain_json(file: ReadableSource) -> Any:
    """Read the JSON content from the given file. Handles gzip-compressed
    content. Returns vanilla JSON.

    Args:
        file: A file path (string) or an open file-like object

    Returns:
        The parsed JSON data structure (dict, list, etc.)

    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If permission is denied to read the file
        OSError: If other I/O errors occur
        json.JSONDecodeError: If the file content is not valid JSON
        ValueError: If file parameter is not a valid type
    """

    return JS.loads(read_content(file))


def read_bookmarks_json(file: ReadableSource) -> Folder:
    """Read the JSON version of bookmarks data from the given input source and
    restore it to a tree structure based on the `Folder` and `Bookmark`
    classes.

    Args:
        file: A file path (string) or an open file-like object

    Returns:
        The root Folder object containing the bookmark tree structure

    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If permission is denied to read the file
        OSError: If other I/O errors occur
        json.JSONDecodeError: If the file content is not valid JSON
        ValueError: If file parameter is not a valid type
    """

    return JS.loads(read_content(file), cls=BookmarksDecoder)


def write_json_data(
    data: Any, file: WritableSource, *,
    json: dict[str, Any] | None = None, gzip: dict[str, Any] | None = None
) -> None:
    """Write the given data as JSON content. Handles gzip-compressing of
    content.

    Args:
        data: The data structure to write as JSON
        file: A file path (string) or an open file-like object
        json: Optional JSON encoder arguments (e.g., indent, sort_keys)
        gzip: Optional gzip compression arguments (e.g., compresslevel)

    Raises:
        FileNotFoundError: If the specified file path cannot be created
        PermissionError: If permission is denied to write the file
        OSError: If other I/O errors occur
        ValueError: If file parameter is not a valid type
    """

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

    if isinstance(file, (TextIO, TextIOWrapper, StringIO)):
        # An existing open file handle. It will be written to directly and we
        # return immediately (without closing the existing handle).
        JS.dump(data, file, **json_args)
        return

    # Input validation for string file paths
    if not isinstance(file, str):
        raise ValueError(
            "File parameter must be a string path or file-like object"
        )

    if not file.strip():
        raise ValueError("File path cannot be empty or whitespace")

    # Case-insensitive compression detection
    is_compressed = file.lower().endswith('.gz')

    try:
        if is_compressed:
            # Gzip'd output - create file handle directly in context manager
            with GZ.open(file, 'wt', **gzip_args) as fh:
                JS.dump(data, fh, **json_args)
        else:
            # Assume plain-text output - create file handle directly
            with open(file, 'w', encoding='utf8') as fh:
                JS.dump(data, fh, **json_args)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Could not create file '{file}'") from exc
    except PermissionError as exc:
        raise PermissionError(
            f"Permission denied when trying to write '{file}'") from exc
    except OSError as e:
        raise OSError(f"I/O error when writing '{file}': {e}") from e
