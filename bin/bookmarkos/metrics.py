"""Home of all metrics-related processing and calculation, etc."""

from bookmarkos.data.bookmarks import Folder, Bookmark
from bookmarkos.data.metrics import Metrics, SizeMetrics


def _gather_metrics(node: Folder, path: list[str], metrics: Metrics) -> None:
    """Recursively gather metrics at folder `node`."""

    # Used to make unique identifier for the folder. THe "::" sequence is used
    # because folder names can (and do) contain "/".
    folder = '::'.join(path)

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


def differentiate_metrics(these: Metrics, those: Metrics | None = None) -> None:
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


def gather_metrics(week: Folder) -> Metrics:
    """Determine the metrics of the given week's data."""

    metrics = Metrics()

    # Start the recursive gathering from `week` (the root folder) with a null
    # folder-name element and the fresh `Metrics` object.
    _gather_metrics(week, [''], metrics)

    # Calculate averages
    metrics.tags.avg_size = average_size(metrics.tags)
    metrics.folders.avg_size = average_size(metrics.folders)

    # Calculate uniqueness of tags
    metrics.tags.unique_tags_count = len(metrics.tags.items)

    return metrics
