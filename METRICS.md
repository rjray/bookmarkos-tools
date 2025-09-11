# Metrics Guide

This is a guide to the metrics that are currently gathered and the metrics that
are planned for future expansion.

## Current Metrics

These are the metrics being gathered in the current implementation.

### Folders Metrics

1. Total count
2. Set of unique identifiers, paths in this case
3. Set of any new folders
4. Count of new folders
5. Set of any deleted folders
6. Count of deleted folders
7. Delta change in folders
8. Delta as a percentage against the basis data
9. Sizes of all folders
10. Smallest folder size
11. Largest folder size
12. Average folder size

Items 3-8 are only calculated when there is a second (basis) data-set to
compare the focus data-set with.

### Bookmarks Metrics

1. Total count
2. Set of unique identifiers, creation-time in this case
3. Set of any new bookmarks
4. Count of new bookmarks
5. Set of any deleted bookmarks
6. Count of deleted bookmarks
7. Delta change in bookmarks
8. Delta as a percentage against the basis data
9. Count of new bookmarks creation by date, within the period being measured

Items 3-9 are only calculated when there is a second (basis) data-set to
compare the focus data-set with.

### Tags Metrics

1. Total count (non-unique)
2. Set of unique identifiers, tag names in this case
3. Count of unique tag names
4. Set of any new tags
5. Count of new tags
6. Set of any deleted tags
7. Count of deleted tags
8. Delta change in unique tags
9. Delta as a percentage against the basis data
10. Sizes/reach of all tags
11. Smallest tag size/reach
12. Largest tag size/reach
13. Average tag size/reach
14. Count of distinct tags' usage by date, within the period being measured

Items 4-9 and 14 are only calculated when there is a second (basis) data-set to
compare the focus data-set with.

## Planned Metrics

These are the metrics that are planned for addition to the above.

### Folders Plans

1. Time each folder appears
2. Number of bookmarks added to a folder over time
3. Top N folders by size (bookmarks only?)
4. Bottom N folders by size (bookmarks only?)
5. Fan-out: max depth, max breadth

### Bookmarks Plans

1. Trace movement of bookmarks between folders
2. Day-based trends in numbers of bookmarks created
3. Time-of-day-based trends in creation

### Tags Plans

1. Time each tag was first used
2. How recently a tag has been used
3. Some sort of clustering analysis of "bursts" of usage of a given tag
4. Top N tags by usage/reach
5. Bottom N tags by usage/reach
6. Identification of groups of tags with low Levenshtein distance
7. Top N tag relations
