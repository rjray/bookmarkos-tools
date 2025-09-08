"""The data classes used for representing various metrics data."""

from dataclasses import dataclass, field
import sys


@dataclass
class CoreMetrics():
    # pylint: disable=too-many-instance-attributes
    """The core metrics that are gathered for bookmarks, tags, and folders."""

    count: int = 0
    items: set = field(default_factory=set)
    added: set = field(default_factory=set)
    added_count: int = 0
    deleted: set = field(default_factory=set)
    deleted_count: int = 0
    delta: int = 0
    delta_pct: float = 0.0


@dataclass
class SizeMetrics():
    """Metrics related to size, used for folders and tags."""

    sizes: dict = field(default_factory=dict)
    min_size: int = sys.maxsize
    max_size: int = 0
    avg_size: float = 0.0


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


@dataclass
class Metrics():
    """This is a data-class for gathering the metrics of a week's data. It
    combines `FoldersMetrics`, `BookmarksMetrics` and `TagsMetrics`."""

    folders: FoldersMetrics = field(default_factory=FoldersMetrics)
    bookmarks: BookmarksMetrics = field(default_factory=BookmarksMetrics)
    tags: TagsMetrics = field(default_factory=TagsMetrics)
    all_bookmarks: list = field(default_factory=list)
