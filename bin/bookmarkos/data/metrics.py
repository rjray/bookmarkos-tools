"""The data classes used for representing various metrics data."""

from collections import Counter
from dataclasses import dataclass, field
import sys

from bookmarkos.data.bookmarks import Bookmark


type SizeRankedList = list[tuple[int, int, list[str]]]
"""A type-alias for the lists of (rank, size, list(names)) tuples used in
`SizeMetrics`."""


@dataclass
class CoreMetrics():
    # pylint: disable=too-many-instance-attributes
    """The core metrics that are gathered for bookmarks, tags, and folders."""

    count: int = 0
    "The total count of the type"
    items: set = field(default_factory=set)
    "A `set` object holding all the identifiers of the type"
    added: set = field(default_factory=set)
    "A `set` object holding all the identifiers added in this dataset"
    added_count: int = 0
    "The count of added elements"
    deleted: set = field(default_factory=set)
    "A `set` object holding all the identifiers deleted in this dataset"
    deleted_count: int = 0
    "The count of deleted elements"
    delta: int = 0
    "The overall change in the number of elements when compared to older data"
    delta_pct: float = 0.0
    "The `delta` value as a percentage-change over the older data"


@dataclass
class SizeMetrics():
    """Metrics related to size, used for folders and tags."""

    sizes: Counter[str] = field(default_factory=Counter)
    "Size of each entity, indexed by name/identifier"
    min_size: int = sys.maxsize
    "Size of the smallest entity"
    max_size: int = 0
    "Size of the largest entity"
    avg_size: float = 0.0
    "Average size of all entities of the type"
    top_n: SizeRankedList = field(
        default_factory=list, compare=False, repr=False
    )
    "The top N items by size, as (rank, size, list(names)) tuples, with ties"
    bottom_n: SizeRankedList = field(
        default_factory=list, compare=False, repr=False
    )
    "The bottom N items by size, as (rank, size, list(names)) tuples, with ties"


@dataclass
class FoldersMetrics(CoreMetrics, SizeMetrics):
    """CoreMetrics+SizeMetrics, plus anything extra needed for folders."""

    max_depth: int = 0
    "Maximum depth of the folder tree"


@dataclass
class BookmarksMetrics(CoreMetrics):
    """CoreMetrics plus anything extra needed for bookmarks."""

    new_bookmarks: list[Bookmark] = field(
        default_factory=list, compare=False, repr=False
    )
    "New bookmarks added in this dataset"
    new_bookmarks_by_date: dict[str, list[int]] = field(
        default_factory=dict, compare=False, repr=False
    )
    "New bookmarks, indexed by their date-added timestamp"


@dataclass
class TagsMetrics(CoreMetrics, SizeMetrics):
    """CoreMetrics+SizeMetrics, plus anything extra needed for tags."""

    unique_tags_count: int = 0
    "A count of the unique tags, separate from the overall tag-count"
    tags_by_date: dict[str, Counter[str]] = field(
        default_factory=dict, compare=False, repr=False
    )
    "Tags on new bookmarks, indexed by the date-added timestamp of the bookmark"


@dataclass
class Metrics():
    """This is a data-class for gathering the metrics of a week's data. It
    combines `FoldersMetrics`, `BookmarksMetrics` and `TagsMetrics`."""

    folders: FoldersMetrics = field(default_factory=FoldersMetrics)
    "Metrics for the folders"
    bookmarks: BookmarksMetrics = field(default_factory=BookmarksMetrics)
    "Metrics for the bookmarks"
    tags: TagsMetrics = field(default_factory=TagsMetrics)
    "Metrics for the tags"
