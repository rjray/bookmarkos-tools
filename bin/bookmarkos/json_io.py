"""Abstract all the input/output of JSON data for the suite of tools."""

import gzip as GZ
from io import TextIOWrapper
import json as JS
from typing import Any, TextIO


class Encoder(JS.JSONEncoder):
    """A wrapper-style class around `JSONEncoder` to handle dict-based objects
    in the structure being converted to JSON."""

    def default(self, o):
        return o.__dict__


def read_json_data(file: str | TextIO | TextIOWrapper) -> Any:
    """Read the JSON content from the given file. Handles gzip-compressed
    content."""

    if isinstance(file, (TextIO, TextIOWrapper)):
        fh = file
    elif file.endswith(".gz"):
        # Gzip'd content
        fh = GZ.open(file, "rb")
    else:
        # Assume plain-text content
        fh = open(file, "r", encoding="utf8")

    with fh:
        data = JS.load(fh)

    return data


def write_json_data(
    data: Any, file: str | TextIO | TextIOWrapper, *, json=None, gzip=None
) -> None:
    """Write the given data as JSON content. Handles gzip-compressing of
    content."""

    json_args: dict[str, Any] = {
        "cls": Encoder,
        "ensure_ascii": False,
    }
    if json is not None:
        json_args |= json
    gzip_args: dict[str, Any] = {
        "compresslevel": 9,
    }
    if gzip is not None:
        gzip_args |= gzip

    if isinstance(file, (TextIO, TextIOWrapper)):
        fh = file
    elif file.endswith(".gz"):
        # Gzip'd output
        fh = GZ.open(file, "wt", **gzip_args)
    else:
        # Assume plain-text output
        fh = open(file, "w", encoding="utf8")

    with fh:
        JS.dump(data, fh, **json_args)
