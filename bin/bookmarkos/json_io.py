"""Abstract all the input/output of JSON data for the suite of tools."""

import gzip as GZ
import json as JS
from typing import Any


class Encoder(JS.JSONEncoder):
    """A wrapper-style class around `JSONEncoder` to handle dict-based objects
    in the structure being converted to JSON."""

    def default(self, o):
        return o.__dict__


def read_json_data(file: str) -> Any:
    """Read the JSON content from the given file. Handles gzip-compressed
    content."""

    if file.endswith(".gz"):
        # Gzip'd content
        fh = GZ.open(file, "rb")
    else:
        # Assume plain-text content
        fh = open(file, "r", encoding="utf8")

    with fh:
        data = JS.load(fh)

    return data


def write_json_data(
    data: Any, file: str, *, json: dict = {}, gzip: dict = {}
) -> None:
    """Write the given data as JSON content. Handles gzip-compressing of
    content."""

    if file.endswith(".gz"):
        # Gzip'd output
        fh = GZ.open(file, "wt", **gzip)
    else:
        # Assume plain-text output
        fh = open(file, "w", encoding="utf8")

    with fh:
        data = JS.dump(data, fh, **json)

    return data
