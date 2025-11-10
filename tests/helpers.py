"""Test utilities and helpers for BookmarkOS Tools tests."""

import gzip
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

# Add the bin directory to Python path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'bin'))


class TestDataGenerator:
    """Generate test data for various test scenarios."""

    @staticmethod
    def create_bookmark_dict(
        name: str = "Test Bookmark",
        url: str = "https://example.com",
        created: int = 1641921698,
        updated: int = 1641921698,
        visited: Optional[int] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        parent: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a bookmark dictionary for testing."""
        if tags is None:
            tags = []
        if parent is None:
            parent = [""]

        bookmark = {
            "name": name,
            "url": url,
            "created": created,
            "updated": updated,
            "visited": visited,
            "tags": tags,
            "notes": notes,
            "parent": parent
        }
        return bookmark

    @staticmethod
    def create_folder_dict(
        name: str = "Test Folder",
        created: int = 1641921698,
        updated: int = 1641921698,
        depth: int = 1,
        content: Optional[List[Dict[str, Any]]] = None,
        parent: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a folder dictionary for testing."""
        if content is None:
            content = []
        if parent is None:
            parent = [""]

        folder = {
            "name": name,
            "created": created,
            "updated": updated,
            "parent": parent,
            "depth": depth,
            "content": content
        }
        return folder

    @staticmethod
    def create_html_bookmark(
        href: str = "https://example.com",
        add_date: str = "1641921698",
        last_modified: str = "1641921698",
        last_visit: Optional[str] = None,
        tags: Optional[str] = None,
        title: str = "Test Bookmark",
        notes: Optional[str] = None
    ) -> str:
        """Create HTML bookmark markup for testing."""
        attrs = [f'HREF="{href}"', f'ADD_DATE="{add_date}"',
                 f'LAST_MODIFIED="{last_modified}"']

        if last_visit:
            attrs.append(f'LAST_VISIT="{last_visit}"')
        if tags:
            attrs.append(f'TAGS="{tags}"')

        html = f'<A {" ".join(attrs)}>{title}</A>'

        if notes:
            html += f'\n    <DD>{notes}'

        return html

    @staticmethod
    def create_html_folder(
        name: str = "Test Folder",
        add_date: str = "1641921698",
        last_modified: str = "1641921698",
        content: str = ""
    ) -> str:
        """Create HTML folder markup for testing."""
        html = f'<H3 ADD_DATE="{add_date}" LAST_MODIFIED="{last_modified}">{name}</H3>\n'
        html += '    <DL><p>\n'
        if content:
            html += content
        html += '    </DL><p>'
        return html


class TempFileHelper:
    """Helper for creating temporary test files."""

    @staticmethod
    def create_temp_html(content: str, compressed: bool = False) -> Path:
        """Create a temporary HTML file with the given content."""
        suffix = '.html.gz' if compressed else '.html'

        with tempfile.NamedTemporaryFile(mode='w' if not compressed else 'wb',
                                         suffix=suffix, delete=False) as f:
            if compressed:
                with gzip.open(f.name, 'wt', encoding='utf-8') as gz_f:
                    gz_f.write(content)
            else:
                f.write(content)
            return Path(f.name)

    @staticmethod
    def create_temp_json(data: Any, compressed: bool = False) -> Path:
        """Create a temporary JSON file with the given data."""
        suffix = '.json.gz' if compressed else '.json'

        with tempfile.NamedTemporaryFile(mode='w' if not compressed else 'wb',
                                         suffix=suffix, delete=False) as f:
            if compressed:
                with gzip.open(f.name, 'wt', encoding='utf-8') as gz_f:
                    json.dump(data, gz_f, ensure_ascii=False, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return Path(f.name)


class MockFactory:
    """Factory for creating various mocks used in tests."""

    @staticmethod
    def create_bookmark_mock(**kwargs) -> Mock:
        """Create a mock bookmark object."""
        defaults = {
            'name': 'Test Bookmark',
            'url': 'https://example.com',
            'created': 1641921698,
            'updated': 1641921698,
            'visited': None,
            'tags': [],
            'notes': None,
            'parent': ['']
        }
        defaults.update(kwargs)

        mock = Mock()
        for key, value in defaults.items():
            setattr(mock, key, value)
        return mock

    @staticmethod
    def create_folder_mock(**kwargs) -> Mock:
        """Create a mock folder object."""
        defaults = {
            'name': 'Test Folder',
            'created': 1641921698,
            'updated': 1641921698,
            'parent': [''],
            'depth': 1,
            'content': []
        }
        defaults.update(kwargs)

        mock = Mock()
        for key, value in defaults.items():
            setattr(mock, key, value)
        return mock

    @staticmethod
    def create_metrics_mock(**kwargs) -> Mock:
        """Create a mock metrics object."""
        mock = Mock()
        mock.bookmarks = Mock()
        mock.folders = Mock()
        mock.tags = Mock()

        # Set default attributes
        for attr in ['count', 'items', 'sizes', 'max_size', 'min_size']:
            setattr(mock.bookmarks, attr, kwargs.get(
                f'bookmarks_{attr}', 0 if 'count' in attr or 'size' in attr else set()))
            setattr(mock.folders, attr, kwargs.get(
                f'folders_{attr}', 0 if 'count' in attr or 'size' in attr else set()))
            setattr(mock.tags, attr, kwargs.get(
                f'tags_{attr}', 0 if 'count' in attr or 'size' in attr else set()))

        return mock


def assert_bookmark_equal(actual: Any, expected: Dict[str, Any], msg: str = ""):
    """Assert that a bookmark object matches expected values."""
    assert actual.name == expected['name'], f"Name mismatch {msg}"
    assert actual.url == expected['url'], f"URL mismatch {msg}"
    assert actual.created == expected[
        'created'], f"Created timestamp mismatch {msg}"
    assert actual.updated == expected[
        'updated'], f"Updated timestamp mismatch {msg}"
    assert actual.visited == expected.get(
        'visited'), f"Visited timestamp mismatch {msg}"
    assert actual.tags == expected.get('tags', []), f"Tags mismatch {msg}"
    assert actual.notes == expected.get('notes'), f"Notes mismatch {msg}"
    assert actual.parent == expected.get(
        'parent', ['']), f"Parent path mismatch {msg}"


def assert_folder_equal(actual: Any, expected: Dict[str, Any], msg: str = ""):
    """Assert that a folder object matches expected values."""
    assert actual.name == expected['name'], f"Name mismatch {msg}"
    assert actual.created == expected[
        'created'], f"Created timestamp mismatch {msg}"
    assert actual.updated == expected[
        'updated'], f"Updated timestamp mismatch {msg}"
    assert actual.depth == expected.get('depth', 0), f"Depth mismatch {msg}"
    assert actual.parent == expected.get(
        'parent', ['']), f"Parent path mismatch {msg}"
    assert len(actual.content) == len(expected.get(
        'content', [])), f"Content length mismatch {msg}"
