# Copilot Instructions for BookmarkOS Tools

## Project Overview

This is a Python toolkit for processing and analyzing [BookmarkOS](https://bookmarkos.com/) backup files. The project converts pseudo-HTML bookmark backups into JSON, calculates metrics, and generates reports on bookmark collection growth and usage patterns.

## Architecture & Core Components

### Data Model (`bookmarkos/data/`)

- **`bookmarks.py`**: Defines the core hierarchy: `Node` → `Folder` → tree structure with `Bookmark` leaves
- **`metrics.py`**: Data classes for metrics collection (`BookmarksMetrics`, `FoldersMetrics`, `TagsMetrics`)
- Uses `@dataclass` pattern with `fill()` methods for parsing pseudo-HTML attributes

### Parser System (`bookmarkos/parser.py`)

- **Critical**: Handles non-standard HTML format from BookmarkOS exports
- Uses regex parsing instead of standard HTML parsers due to malformed markup
- Recursive descent parser: `process_folder()` → `process_dt()` for `<A>`/`<H3>` tags
- Preserves hierarchical structure with depth tracking and parent paths

### I/O Layer (`bookmarkos/json_io.py`)

- **Auto-compression**: File extension `.gz` triggers gzip compression/decompression
- Custom JSON encoder/decoder for object reconstruction (`BasicEncoder`, `BookmarksDecoder`)
- Handles both file paths and open file handles uniformly

### Metrics Engine (`bookmarkos/metrics.py`)

- **Key function**: `gather_metrics()` calculates comprehensive bookmark statistics
- **Differential analysis**: `differentiate_metrics()` compares two datasets for weekly reports
- Uses BFS traversal for collecting folder sizes (bookmarks only, excluding subfolders)
- Implements ranking with tie-handling for top/bottom lists

## Command-Line Tools (in `bin/`)

### `bookmarks2json`

Primary converter: pseudo-HTML → JSON structure

```bash
bookmarks2json --input backup.html --output bookmarks.json.gz --pretty
```

### `bookmarks_report`

Metrics analysis and reporting (weekly reports currently implemented)

### `process_bookmarks`

Automated workflow script (runs as cron job):

- Compresses weekly backup from Dropbox
- Converts to JSON
- Generates and emails weekly report

## Development Patterns

### File Naming Convention

- Backup files: `bookmarks-YYYYMMDD.html.gz`
- JSON files: `bookmarks-YYYYMMDD.json.gz`
- Configuration: `config/bookmarkos-tools.toml`

### Error Handling

- Parser raises `ValueError` with descriptive messages for malformed input
- File operations auto-detect compression from extensions
- UTF-8 encoding enforced throughout

### Testing Strategy

No formal test suite exists yet (see TODO.md), but the parser is designed to handle:

- Missing closing tags in pseudo-HTML
- Depth-based folder nesting validation
- UNIX timestamp conversion for dates

## Key Integration Points

### Time Handling

- All timestamps are UNIX epochs (seconds since 1970-01-01 UTC)
- Date grouping uses `YYYY-MM-DD` format for reporting
- `datetime.fromtimestamp(..., tz=timezone.utc)` for conversions

### Configuration System

- TOML-based config in `config/bookmarkos-tools.toml`
- Planned integration (currently tools use command-line args)

### External Dependencies

- Dropbox integration via `process_bookmarks` script
- Email reporting via `mailx` command
- Gzip compression for storage efficiency

## Working with This Codebase

### Adding New Metrics

1. Extend data classes in `bookmarkos/data/metrics.py`
2. Add calculation logic in `gather_metrics()` or `differentiate_metrics()`
3. Update report generators to display new metrics

### Parser Modifications

- Understand the regex patterns in `EXTRACTION_RE` and `ATTRIB_RE`
- Maintain the recursive folder processing in `process_folder()`
- Test with actual BookmarkOS backup files (malformed HTML)

### New Tool Development

- Follow the pattern: parse args → use `bookmarkos.parser.parse_bookmarks()` → process → use `bookmarkos.json_io` for output
- Leverage existing metrics calculations in `bookmarkos.metrics`
