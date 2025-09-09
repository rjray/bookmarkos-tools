"""The data classes used for representing various metrics data."""

from dataclasses import dataclass, field
import sys


@dataclass
class CoreMetrics():
    # pylint: disable=too-many-instance-attributes
    """The core metrics that are gathered for bookmarks, tags, and folders."""

    count: int = 0
    "The total count of the type"
    items: set = field(default_factory=set)
    "A `Set` holding all the identifiers of the type"
    added: set = field(default_factory=set)
    "A `Set` holding all the identifiers of those added in this dataset"
    added_count: int = 0
    "The count of added elements"
    deleted: set = field(default_factory=set)
    "A `Set` holding all the identifiers of those deleted in this dataset"
    deleted_count: int = 0
    "The count of deleted elements"
    delta: int = 0
    "The overall change in the number of elements when compared to older data"
    delta_pct: float = 0.0
    "The `delta` value as a percentage-change over the older data"


@dataclass
class SizeMetrics():
    """Metrics related to size, used for folders and tags."""

    sizes: dict = field(default_factory=dict)
    "Size of each entity, indexed by name/identifier"
    min_size: int = sys.maxsize
    "Size of the smallest entity"
    max_size: int = 0
    "Size of the largest entity"
    avg_size: float = 0.0
    "Average size of all entities of the type"


@dataclass
class FoldersMetrics(CoreMetrics, SizeMetrics):
    """CoreMetrics+SizeMetrics, plus anything extra needed for folders."""


@dataclass
class BookmarksMetrics(CoreMetrics):
    """CoreMetrics plus anything extra needed for bookmarks."""


@dataclass
class TagsMetrics(CoreMetrics, SizeMetrics):
    """CoreMetrics+SizeMetrics, plus anything extra needed for tags."""

    unique_tags_count: int = 0
    "A count of the unique tags, separate from the overall tag-count"


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
