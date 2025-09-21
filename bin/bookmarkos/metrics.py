"""Home of all metrics-related processing and calculation, etc."""

from bisect import bisect_left
from collections import Counter
from datetime import datetime, timezone
from itertools import groupby
from operator import attrgetter, itemgetter

from bookmarkos.data.bookmarks import Folder, Bookmark, FolderContent
from bookmarkos.data.metrics import Metrics, SizeMetrics, SizeRankedList


def get_largest_and_smallest(
        sizes: Counter[str], n: int
) -> tuple[SizeRankedList, SizeRankedList]:
    """Return the N largest and smallest items from the `sizes` Counter object,
    as two lists of (name, size, rank) tuples. Ties are handled, and ties may
    cause the displayed lists to be longer than N."""

    largest: SizeRankedList = []
    smallest: SizeRankedList = []

    # Sort the elements by size.
    sorted_sizes = sorted(sizes.items(), key=lambda x: x[1], reverse=True)
    # Use `groupby` to group the elements by size, so that we can assign
    # ranks properly (i.e., if two elements have the same size, they get the
    # same rank).
    grouped = []
    for size, group in groupby(sorted_sizes, key=itemgetter(1)):
        grouped.append((size, list(group)))
    # Now assign ranks and build a list that accounts for ties.
    ranked_with_ties: SizeRankedList = []
    current_rank = 1
    for size, group in grouped:
        ranked_with_ties.append(
            (current_rank, size, sorted([name for name, _ in group]))
        )
        current_rank += len(group)

    # Now extract the largest N and smallest N, accounting for ties.
    lg_count = 0
    sm_count = 0
    for item in ranked_with_ties:
        rank, size, names = item
        if lg_count < n:
            largest.append((rank, size, names))
            lg_count += len(names)
        if lg_count >= n:
            break
    for item in reversed(ranked_with_ties):
        rank, size, names = item
        if sm_count < n:
            smallest.append((rank, size, names))
            sm_count += len(names)
        if sm_count >= n:
            break

    return largest, list(reversed(smallest))


def _gather_metrics(node: Folder, path: list[str], metrics: Metrics) -> None:
    """Recursively gather metrics at folder `node`."""

    # Used to make unique identifier for the folder. The "::" sequence is used
    # because folder names can (and do) contain "/".
    folder = '::'.join(path)

    # Update maximum depth
    metrics.folders.max_depth = max(metrics.folders.max_depth, node.depth)

    # Get the size, then separate content into bookmarks and sub-folders.
    folder_size = len(node.content)
    bookmarks = [x for x in node.content if isinstance(x, Bookmark)]
    subfolders = [x for x in node.content if isinstance(x, Folder)]

    # Folder-oriented metrics
    metrics.folders.count += 1
    metrics.folders.items.add(folder)
    metrics.folders.sizes[folder] = folder_size
    metrics.folders.max_size = max(metrics.folders.max_size, folder_size)
    metrics.folders.min_size = min(metrics.folders.min_size, folder_size)

    # Process bookmarks, for bookmark-oriented and tag-oriented metrics
    metrics.bookmarks.count += len(bookmarks)
    for bookmark in bookmarks:
        metrics.bookmarks.items.add(bookmark.created)

        num_tags = len(bookmark.tags)
        metrics.tags.count += num_tags
        metrics.tags.max_size = max(metrics.tags.max_size, num_tags)
        metrics.tags.min_size = min(metrics.tags.min_size, num_tags)

        for tag in bookmark.tags:
            metrics.tags.items.add(tag)
            metrics.tags.sizes[tag] += 1

    for subfolder in subfolders:
        # Seems the only way to prevent corruption of the `path` list is to
        # explicitly copy it and append the new name.
        newpath = path.copy()
        newpath.append(subfolder.name)
        _gather_metrics(subfolder, newpath, metrics)


def average_size(metrics: SizeMetrics) -> float:
    """Calculate the average size for either `folders` or `tags`."""

    sizes = metrics.sizes
    count = len(sizes)
    total = sum(sizes[x] for x in sizes.keys())

    return total / count


def new_bookmarks_by_date(metrics: Metrics) -> dict[str, list[int]]:
    """Return a dictionary of the new bookmarks, indexed by their date-added
    timestamp (YYYY-MM-DD)."""

    by_date: dict[str, list[int]] = {}

    for bookmark_id in sorted(metrics.bookmarks.added):
        # Convert the bookmark ID (which is a UNIX timestamp) into a date
        # string of the form "YYYY-MM-DD".

        dt = datetime.fromtimestamp(bookmark_id, tz=timezone.utc)
        date_str = dt.strftime('%Y-%m-%d')

        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append(bookmark_id)

    return by_date


def tags_usage_by_date(metrics: Metrics) -> dict[str, Counter[str]]:
    """Return a dictionary of tags used on new bookmarks, indexed by the
    date-added timestamp (YYYY-MM-DD) of the bookmark. The `bookmarks` argument
    is the root folder of the dataset, used for referencing the new bookmarks
    for their tags."""

    by_date: dict[str, Counter[str]] = {}

    for bookmark in metrics.bookmarks.new_bookmarks:
        # Convert the bookmark ID (which is a UNIX timestamp) into a date
        # string of the form "YYYY-MM-DD".

        dt = datetime.fromtimestamp(bookmark.created).astimezone(timezone.utc)
        date_str = dt.strftime('%Y-%m-%d')

        if date_str not in by_date:
            by_date[date_str] = Counter()

        for tag in bookmark.tags:
            by_date[date_str][tag] += 1

    return by_date


def all_bookmarks_sorted(data: Folder) -> list[Bookmark]:
    """Create a list of all bookmarks in `data`, sorted by the creation time.
    Uses an iterative BFS approach."""

    bookmarks: list[Bookmark] = []
    queue: FolderContent = data.content[:]

    while len(queue) > 0:
        item = queue.pop(0)

        if isinstance(item, Bookmark):
            bookmarks.append(item)
        else:
            queue += item.content

    bookmarks.sort(key=attrgetter('created'))
    return bookmarks


def differentiate_metrics(
        this_week: Folder,
        these: Metrics,
        those: Metrics | None = None
) -> None:
    """Calculate the additional values (differences, etc.) between two sets of
    metrics. These values only update the metrics of `these`. If `those` is
    `None`, then all differentials are set to represent initial data values."""

    if those is not None:
        # Additional values for bookmarks
        bookmarks = these.bookmarks
        bookmarks.delta = bookmarks.count - those.bookmarks.count
        if those.bookmarks.count == 0:
            bookmarks.delta_pct = 1.0
        else:
            bookmarks.delta_pct = bookmarks.delta / those.bookmarks.count
        bookmarks.added = bookmarks.items - those.bookmarks.items
        bookmarks.added_count = len(bookmarks.added)
        bookmarks.deleted = those.bookmarks.items - bookmarks.items
        bookmarks.deleted_count = len(bookmarks.deleted)

        # Additional values for folders
        folders = these.folders
        folders.delta = folders.count - those.folders.count
        if those.folders.count == 0:
            folders.delta_pct = 1.0
        else:
            folders.delta_pct = folders.delta / those.folders.count
        folders.added = folders.items - those.folders.items
        folders.added_count = len(folders.added)
        folders.deleted = those.folders.items - folders.items
        folders.deleted_count = len(folders.deleted)

        # Additional values for tags
        tags = these.tags
        this_tags = tags.items
        last_tags = those.tags.items
        len_this = len(this_tags)
        len_last = len(last_tags)
        tags.delta = len_this - len_last
        if len_last == 0:
            tags.delta_pct = 0.0 if len_this == 0 else 1.0
        else:
            tags.delta_pct = tags.delta / len_last
        tags.added = this_tags - last_tags
        tags.added_count = len(tags.added)
        tags.deleted = last_tags - this_tags
        tags.deleted_count = len(tags.deleted)
    else:
        # If this is called with no value for `those`, then this represents
        # the very initial bookmarks set. Assign the values appropriately.

        # Bookmarks
        bookmarks = these.bookmarks
        bookmarks.delta = bookmarks.count
        bookmarks.delta_pct = 1.0 if bookmarks.count != 0 else 0.0
        bookmarks.added = bookmarks.items.copy()
        bookmarks.added_count = bookmarks.count
        bookmarks.deleted = set()
        bookmarks.deleted_count = 0

        # Folders
        folders = these.folders
        folders.delta = folders.count
        folders.delta_pct = 1.0 if folders.count != 0 else 0.0
        folders.added = folders.items.copy()
        folders.added_count = folders.count
        folders.deleted = set()
        folders.deleted_count = 0

        # Tags
        tags = these.tags
        this_tags = tags.items
        tags.delta = len(this_tags)
        tags.delta_pct = 1.0 if tags.delta != 0 else 0.0
        tags.added = this_tags.copy()
        tags.added_count = len(this_tags)
        tags.deleted = set()
        tags.deleted_count = 0

    # Generate some of the aggregrated values.

    # Bookmark objects for the new bookmarks
    all_bookmarks = all_bookmarks_sorted(this_week)
    these.bookmarks.new_bookmarks = []
    for bookmark_id in sorted(these.bookmarks.added):
        pos = bisect_left(
            all_bookmarks, bookmark_id, key=attrgetter('created')
        )
        these.bookmarks.new_bookmarks.append(all_bookmarks[pos])
    # New bookmarks by date
    these.bookmarks.new_bookmarks_by_date = new_bookmarks_by_date(these)
    # New bookmarks' tag usage by date
    these.tags.tags_by_date = tags_usage_by_date(these)


def gather_metrics(week: Folder) -> Metrics:
    """Determine the metrics of the given week's data."""

    metrics = Metrics()

    # Start the recursive gathering from `week` (the root folder) with a null
    # folder-name element and the fresh `Metrics` object.
    _gather_metrics(week, [''], metrics)

    # Averages
    metrics.tags.avg_size = average_size(metrics.tags)
    metrics.folders.avg_size = average_size(metrics.folders)

    # Uniqueness of tags
    metrics.tags.unique_tags_count = len(metrics.tags.items)

    # Top and bottom folders by size (5). We want this to be based on just the
    # number of bookmarks in the folder, not including sub-folders.
    folder_sizes: Counter[str] = Counter()
    # BFS over (folder, path_parts). Start like _gather_metrics (root path is
    # ['']).
    queue: list[tuple[Folder, list[str]]] = [(week, [''])]
    while queue:
        folder, path = queue.pop(0)
        parts = [*path, folder.name]
        folder_id = '::'.join(p for p in parts if p)  # empty string for root
        bookmarks_in_folder = 0
        for item in folder.content:
            if isinstance(item, Folder):
                queue.append((item, parts))
            else:
                bookmarks_in_folder += 1
        folder_sizes[folder_id] = bookmarks_in_folder

    metrics.folders.top_n, metrics.folders.bottom_n = (
        get_largest_and_smallest(folder_sizes, 5)
    )
    # Top and bottom tags by size (25)
    metrics.tags.top_n, metrics.tags.bottom_n = (
        get_largest_and_smallest(metrics.tags.sizes, 25)
    )

    return metrics
