"""Home of all metrics-related processing and calculation, etc."""

from bisect import bisect_left
from collections import Counter, deque
from datetime import datetime, timezone
from itertools import groupby
from operator import attrgetter, itemgetter
from typing import Dict, List, Tuple, Set

from bookmarkos.data.bookmarks import Folder, Bookmark
from bookmarkos.data.metrics import Metrics, SizeMetrics, SizeRankedList


def get_largest_and_smallest(
        sizes: Counter[str], n: int
) -> tuple[SizeRankedList, SizeRankedList]:
    """Return the N largest and smallest items from the `sizes` Counter object,
    as two lists of (name, size, rank) tuples. Ties are handled, and ties may
    cause the displayed lists to be longer than N.

    Args:
        sizes: Counter object mapping names to their sizes
        n: Number of items to return in each list

    Returns:
        Tuple of (largest, smallest) ranked lists
    """
    if not sizes:
        return [], []

    largest: SizeRankedList = []
    smallest: SizeRankedList = []

    # Sort the elements by size.
    sorted_sizes = sorted(sizes.items(), key=itemgetter(1), reverse=True)

    # Group by size for proper rank assignment
    ranked_with_ties: SizeRankedList = []
    current_rank = 1

    for size, group in groupby(sorted_sizes, key=itemgetter(1)):
        group_items = list(group)
        ranked_with_ties.append(
            (current_rank, size, sorted([name for name, _ in group_items]))
        )
        current_rank += len(group_items)

    # Extract the largest N and smallest N, accounting for ties.
    largest_count = 0
    smallest_count = 0

    for rank, size, names in ranked_with_ties:
        if largest_count < n:
            largest.append((rank, size, names))
            largest_count += len(names)
        if largest_count >= n:
            break

    for rank, size, names in reversed(ranked_with_ties):
        if smallest_count < n:
            smallest.append((rank, size, names))
            smallest_count += len(names)
        if smallest_count >= n:
            break

    return largest, list(reversed(smallest))


def _gather_metrics(
        node: Folder, path: List[str], metrics: Metrics
) -> Counter[str]:
    """Recursively gather metrics at folder `node`.

    Args:
        node: Current folder being processed
        path: Path to current folder as list of folder names
        metrics: Metrics object to update

    Returns:
        Counter mapping IDs to their bookmark counts (excluding subfolders)
    """
    # Used to make unique identifier for the folder. The "::" sequence is used
    # because folder names can (and do) contain "/".
    folder_id = '::'.join(path)

    # Update maximum depth
    metrics.folders.max_depth = max(metrics.folders.max_depth, node.depth)

    # Get the size, then separate content into bookmarks and sub-folders.
    folder_size = len(node.content)
    bookmarks = [x for x in node.content if isinstance(x, Bookmark)]
    subfolders = [x for x in node.content if isinstance(x, Folder)]

    # Count of bookmarks only (for ranking purposes)
    bookmark_count = len(bookmarks)

    # Folder-oriented metrics
    metrics.folders.count += 1
    metrics.folders.items.add(folder_id)
    metrics.folders.sizes[folder_id] = folder_size
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

    # Initialize folder sizes counter for this level
    folder_sizes: Counter[str] = Counter()
    folder_sizes[folder_id] = bookmark_count

    # Recurse into subfolders
    for subfolder in subfolders:
        # Create new path for subfolder
        newpath = path + [subfolder.name]
        subfolder_sizes = _gather_metrics(subfolder, newpath, metrics)
        folder_sizes.update(subfolder_sizes)

    return folder_sizes


def average_size(metrics: SizeMetrics) -> float:
    """Calculate the average size for either `folders` or `tags`.

    Args:
        metrics: SizeMetrics object containing sizes

    Returns:
        Average size, or 0.0 if no items exist

    Raises:
        ValueError: If metrics.sizes is None
    """
    if metrics.sizes is None:
        raise ValueError("Metrics sizes cannot be None")

    sizes = metrics.sizes
    count = len(sizes)

    if count == 0:
        return 0.0

    total = sum(sizes.values())
    return total / count


def new_bookmarks_by_date(metrics: Metrics) -> Dict[str, List[int]]:
    """Return a dictionary of the new bookmarks, indexed by their date-added
    timestamp (YYYY-MM-DD).

    Args:
        metrics: Metrics object containing bookmark data

    Returns:
        Dictionary mapping date strings to lists of bookmark IDs
    """
    by_date: Dict[str, List[int]] = {}

    for bookmark_id in sorted(metrics.bookmarks.added):
        # Convert the bookmark ID (which is a UNIX timestamp) into a date
        # string of the form "YYYY-MM-DD".
        dt = datetime.fromtimestamp(bookmark_id, tz=timezone.utc)
        date_str = dt.strftime('%Y-%m-%d')

        by_date.setdefault(date_str, []).append(bookmark_id)

    return by_date


def tags_usage_by_date(metrics: Metrics) -> Dict[str, Counter[str]]:
    """Return a dictionary of tags used on new bookmarks, indexed by the
    date-added timestamp (YYYY-MM-DD) of the bookmark.

    Args:
        metrics: Metrics object containing new bookmark data

    Returns:
        Dictionary mapping date strings to Counter objects of tag usage
    """
    by_date: Dict[str, Counter[str]] = {}

    for bookmark in metrics.bookmarks.new_bookmarks:
        # Convert the bookmark created timestamp into a date string
        dt = datetime.fromtimestamp(bookmark.created, tz=timezone.utc)
        date_str = dt.strftime('%Y-%m-%d')

        if date_str not in by_date:
            by_date[date_str] = Counter()

        for tag in bookmark.tags:
            by_date[date_str][tag] += 1

    return by_date


def all_bookmarks_sorted(data: Folder) -> List[Bookmark]:
    """Create a list of all bookmarks in `data`, sorted by the creation time.
    Uses an iterative BFS approach with efficient queue operations.

    Args:
        data: Root folder to traverse

    Returns:
        List of all bookmarks sorted by creation timestamp
    """
    bookmarks: List[Bookmark] = []
    queue: deque[Folder | Bookmark] = deque(data.content)

    while queue:
        item = queue.popleft()

        if isinstance(item, Bookmark):
            bookmarks.append(item)
        elif isinstance(item, Folder):
            queue.extend(item.content)

    bookmarks.sort(key=attrgetter('created'))
    return bookmarks


def _calculate_delta_metrics(
    current_count: int,
    previous_count: int,
    current_items: Set,
    previous_items: Set | None = None
) -> Tuple[int, float, Set, int, Set, int]:
    """Calculate delta metrics between current and previous datasets.

    Args:
        current_count: Current item count
        previous_count: Previous item count (0 for initial data)
        current_items: Set of current items
        previous_items: Set of previous items (None for initial data)

    Returns:
        Tuple of (delta, delta_pct, added, added_count, deleted, deleted_count)
    """
    delta = current_count - previous_count

    if previous_count == 0:
        delta_pct = 1.0 if current_count != 0 else 0.0
    else:
        delta_pct = delta / previous_count

    if previous_items is not None:
        added = current_items - previous_items
        deleted = previous_items - current_items
    else:
        added = current_items.copy()
        deleted = set()

    return delta, delta_pct, added, len(added), deleted, len(deleted)


def differentiate_metrics(
        this_week: Folder,
        these: Metrics,
        those: Metrics | None = None
) -> None:
    """Calculate the additional values (differences, etc.) between two sets of
    metrics. These values only update the metrics of `these`. If `those` is
    `None`, then all differentials are set to represent initial data values.

    Args:
        this_week: Current week's folder data
        these: Current metrics to update
        those: Previous metrics for comparison (None for initial data)
    """
    # Handle bookmarks metrics
    bookmarks = these.bookmarks
    prev_bookmarks = those.bookmarks if those else None
    prev_count = prev_bookmarks.count if prev_bookmarks else 0
    prev_items = prev_bookmarks.items if prev_bookmarks else None

    (bookmarks.delta, bookmarks.delta_pct, bookmarks.added,
     bookmarks.added_count, bookmarks.deleted, bookmarks.deleted_count) = \
        _calculate_delta_metrics(bookmarks.count, prev_count,
                                 bookmarks.items, prev_items)

    # Handle folders metrics
    folders = these.folders
    prev_folders = those.folders if those else None
    prev_count = prev_folders.count if prev_folders else 0
    prev_items = prev_folders.items if prev_folders else None

    (folders.delta, folders.delta_pct, folders.added,
     folders.added_count, folders.deleted, folders.deleted_count) = \
        _calculate_delta_metrics(folders.count, prev_count,
                                 folders.items, prev_items)

    # Handle tags metrics (special case for unique count)
    tags = these.tags
    prev_tags = those.tags if those else None
    current_unique_count = len(tags.items)
    prev_unique_count = len(prev_tags.items) if prev_tags else 0
    prev_items = prev_tags.items if prev_tags else None

    (tags.delta, tags.delta_pct, tags.added,
     tags.added_count, tags.deleted, tags.deleted_count) = \
        _calculate_delta_metrics(current_unique_count, prev_unique_count,
                                 tags.items, prev_items)

    # Generate aggregated values
    _generate_aggregated_metrics(this_week, these)


def _generate_aggregated_metrics(this_week: Folder, metrics: Metrics) -> None:
    """Generate aggregated metric values like new bookmarks by date.

    Args:
        this_week: Current week's folder data
        metrics: Metrics object to update with aggregated values
    """
    # Bookmark objects for the new bookmarks
    all_bookmarks = all_bookmarks_sorted(this_week)
    metrics.bookmarks.new_bookmarks = []

    for bookmark_id in sorted(metrics.bookmarks.added):
        pos = bisect_left(
            all_bookmarks, bookmark_id, key=attrgetter('created')
        )
        metrics.bookmarks.new_bookmarks.append(all_bookmarks[pos])

    # New bookmarks by date
    metrics.bookmarks.new_bookmarks_by_date = new_bookmarks_by_date(metrics)
    # New bookmarks' tag usage by date
    metrics.tags.tags_by_date = tags_usage_by_date(metrics)


def gather_metrics(week: Folder) -> Metrics:
    """Determine the metrics of the given week's data.

    Args:
        week: Root folder to analyze

    Returns:
        Metrics object containing all calculated statistics
    """
    metrics = Metrics()

    # Start the recursive gathering from `week` (the root folder) with a null
    # folder-name element and the fresh `Metrics` object.
    folder_sizes = _gather_metrics(week, [''], metrics)

    # Calculate averages (with safety checks)
    metrics.tags.avg_size = average_size(metrics.tags)
    metrics.folders.avg_size = average_size(metrics.folders)

    # Uniqueness of tags
    metrics.tags.unique_tags_count = len(metrics.tags.items)

    # Top and bottom folders by size (5) - use the sizes collected during
    # traversal
    metrics.folders.top_n, metrics.folders.bottom_n = (
        get_largest_and_smallest(folder_sizes, 5)
    )
    # Top and bottom tags by size (25)
    metrics.tags.top_n, metrics.tags.bottom_n = (
        get_largest_and_smallest(metrics.tags.sizes, 25)
    )

    return metrics
