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
            if tag not in metrics.tags.sizes:
                metrics.tags.sizes[tag] = 1
            else:
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


def differentiate_metrics(these: Metrics, those: Metrics):
    """Calculate the additional values (differences, etc.) between two sets of
    metrics. These values only update the metrics of `these`."""

    # Additional values for bookmarks
    these.bookmarks.delta = \
        these.bookmarks.count - those.bookmarks.count
    these.bookmarks.delta_pct = \
        these.bookmarks.delta / those.bookmarks.count
    these.bookmarks.added = \
        these.bookmarks.items - those.bookmarks.items
    these.bookmarks.added_count = len(these.bookmarks.added)
    these.bookmarks.deleted = \
        those.bookmarks.items - these.bookmarks.items
    these.bookmarks.deleted_count = len(these.bookmarks.deleted)

    # Additional values for folders
    these.folders.delta = these.folders.count - those.folders.count
    these.folders.delta_pct = \
        these.folders.delta / those.folders.count
    these.folders.added = these.folders.items - those.folders.items
    these.folders.added_count = len(these.folders.added)
    these.folders.deleted = \
        those.folders.items - these.folders.items
    these.folders.deleted_count = len(these.folders.deleted)

    # Additional values for tags
    this_tags = these.tags.items
    last_tags = those.tags.items
    these.tags.unique_tags_count = len(this_tags)
    those.tags.unique_tags_count = len(last_tags)
    these.tags.delta = these.tags.unique_tags_count - \
        those.tags.unique_tags_count
    these.tags.delta_pct = \
        these.tags.delta / those.tags.unique_tags_count
    these.tags.added = this_tags - last_tags
    these.tags.added_count = len(these.tags.added)
    these.tags.deleted = last_tags - this_tags
    these.tags.deleted_count = len(these.tags.deleted)


def gather_metrics(week: Folder) -> Metrics:
    """Determine the metrics of the given week's data."""

    metrics = Metrics()

    # Start the recursive gathering from `week` (the root folder) with a null
    # folder-name element and the fresh `Metrics` object.
    _gather_metrics(week, [''], metrics)

    # Calculate averages
    metrics.tags.avg_size = average_size(metrics.tags)
    metrics.folders.avg_size = average_size(metrics.folders)

    return metrics
