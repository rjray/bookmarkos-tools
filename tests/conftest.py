"""Shared pytest fixtures and configuration for BookmarkOS Tools tests."""

import os
from pathlib import Path
import sys
import tempfile
from typing import Generator, Dict, Any
from unittest.mock import Mock

import pytest

# Add the bin directory to the Python path for imports
bin_path = os.path.join(os.path.dirname(__file__), '..', 'bin')
if bin_path not in sys.path:
    sys.path.insert(0, bin_path)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_bookmark_html() -> str:
    """Sample BookmarkOS HTML content for testing."""
    return '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><A HREF="https://github.com/rjray/bookmarkos-tools"
           ADD_DATE="1641921698"
           LAST_VISIT="1648322750"
           LAST_MODIFIED="1755453381"
           TAGS="github, python, tools">BookmarkOS Tools Repository</A>
    <DD>Python toolkit for processing BookmarkOS backup files
    <DT><H3 ADD_DATE="1534112986" LAST_MODIFIED="1563985394">Development</H3>
    <DL><p>
        <DT><A HREF="https://python.org"
               ADD_DATE="1534112990"
               LAST_MODIFIED="1563985400"
               TAGS="python, programming">Python Official Site</A>
        <DT><A HREF="https://pytest.org"
               ADD_DATE="1534112995"
               LAST_MODIFIED="1563985405"
               TAGS="python, testing">Pytest Documentation</A>
    </DL><p>
    <DT><H3 ADD_DATE="1534113000" LAST_MODIFIED="1563985410">Tools</H3>
    <DL><p>
        <DT><A HREF="https://github.com"
               ADD_DATE="1534113005"
               LAST_MODIFIED="1563985415"
               TAGS="git, development">GitHub</A>
    </DL><p>
</DL><p>'''


@pytest.fixture
def malformed_bookmark_html() -> str:
    """Sample malformed BookmarkOS HTML for testing error handling."""
    return '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><A HREF="https://example.com"
           ADD_DATE="1641921698">Missing closing tag
    <DT><H3 ADD_DATE="1534112986">Folder without closing DL</H3>
    <DL><p>
        <DT><A HREF="https://test.com"
               ADD_DATE="1534112990">Another bookmark</A>
    <!-- Missing </DL><p> for folder -->
</DL><p>'''


@pytest.fixture
def sample_json_data() -> Dict[str, Any]:
    """Sample bookmark data in JSON format for testing."""
    return {
        "name": "",
        "created": 0,
        "updated": 0,
        "parent": [],
        "depth": 0,
        "content": [
            {
                "name": "BookmarkOS Tools Repository",
                "url": "https://github.com/rjray/bookmarkos-tools",
                "created": 1641921698,
                "updated": 1755453381,
                "visited": 1648322750,
                "tags": ["github", "python", "tools"],
                "notes": "Python toolkit for processing BookmarkOS backup files",
                "parent": [""]
            },
            {
                "name": "Development",
                "created": 1534112986,
                "updated": 1563985394,
                "parent": [""],
                "depth": 1,
                "content": [
                    {
                        "name": "Python Official Site",
                        "url": "https://python.org",
                        "created": 1534112990,
                        "updated": 1563985400,
                        "visited": None,
                        "tags": ["python", "programming"],
                        "notes": None,
                        "parent": ["", "Development"]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing without actual file I/O."""
    mock_open = Mock()
    mock_gzip_open = Mock()
    mock_json_loads = Mock()
    mock_json_dumps = Mock()

    return {
        'open': mock_open,
        'gzip.open': mock_gzip_open,
        'json.loads': mock_json_loads,
        'json.dumps': mock_json_dumps
    }


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


# Test data constants that can be imported by test modules
SAMPLE_UNIX_TIMESTAMPS = [
    1641921698,  # 2022-01-11 16:01:38 UTC
    1534112986,  # 2018-08-12 21:56:26 UTC
    1648322750,  # 2022-03-26 20:45:50 UTC
]

SAMPLE_TAGS = [
    "python",
    "github",
    "programming",
    "tools",
    "testing",
    "development",
    "git"
]

SAMPLE_URLS = [
    "https://github.com/rjray/bookmarkos-tools",
    "https://python.org",
    "https://pytest.org",
    "https://github.com"
]
