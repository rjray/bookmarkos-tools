# pylint: disable=missing-function-docstring, missing-class-docstring, invalid-name, no-member, import-error, line-too-long

"""Unit tests for bookmarkos.metrics module."""

from collections import Counter
from unittest.mock import Mock, patch
from bookmarkos.metrics import (
    get_largest_and_smallest, average_size, new_bookmarks_by_date,
    tags_usage_by_date, all_bookmarks_sorted, differentiate_metrics,
    gather_metrics
)

import pytest


class TestGetLargestAndSmallest:
    """Tests for the get_largest_and_smallest function."""

    @pytest.mark.metrics
    def test_get_largest_and_smallest_basic(self):
        """Test basic functionality with simple sizes."""
        sizes = Counter({
            "item1": 10,
            "item2": 5,
            "item3": 15,
            "item4": 3,
            "item5": 8
        })

        largest, smallest = get_largest_and_smallest(sizes, 2)

        # Largest should be item3 (15) and item1 (10)
        assert len(largest) == 2
        assert largest[0] == (1, 15, ["item3"])
        assert largest[1] == (2, 10, ["item1"])

        # Smallest should be item2 (5) and item4 (3) - note order and ranks
        assert len(smallest) == 2
        assert smallest[0] == (4, 5, ["item2"])  # Rank 4 (4th overall)
        assert smallest[1] == (5, 3, ["item4"])  # Rank 5 (5th overall)

    @pytest.mark.metrics
    def test_get_largest_and_smallest_with_ties(self):
        """Test handling of tied values."""
        sizes = Counter({
            "item1": 10,
            "item2": 10,  # Tie for first
            "item3": 5,
            "item4": 5,   # Tie for third
            "item5": 1
        })

        largest, smallest = get_largest_and_smallest(sizes, 2)

        # Both items with size 10 should be ranked 1, taking up 2 slots
        assert len(largest) == 1  # Only one group due to ties
        assert largest[0] == (1, 10, ["item1", "item2"])

        # Check smallest rankings - should have both tie groups
        assert len(smallest) == 2
        # Rank 3 (after 2 tied at rank 1)
        assert smallest[0] == (3, 5, ["item3", "item4"])
        assert smallest[1] == (5, 1, ["item5"])  # Rank 5

    @pytest.mark.metrics
    def test_get_largest_and_smallest_empty_counter(self):
        """Test with empty counter."""
        sizes = Counter()

        largest, smallest = get_largest_and_smallest(sizes, 5)

        assert largest == []
        assert smallest == []

    @pytest.mark.metrics
    def test_get_largest_and_smallest_more_requested_than_available(self):
        """Test when requesting more items than available."""
        sizes = Counter({"item1": 5, "item2": 3})

        largest, smallest = get_largest_and_smallest(sizes, 5)

        # Should return all available items
        assert len(largest) == 2
        assert len(smallest) == 2
        assert largest[0] == (1, 5, ["item1"])
        assert largest[1] == (2, 3, ["item2"])


class TestAverageSize:
    """Tests for the average_size function."""

    @pytest.mark.metrics
    def test_average_size_basic(self):
        """Test basic average calculation."""
        mock_metrics = Mock()
        mock_metrics.sizes = Counter({"a": 10, "b": 20, "c": 30})

        result = average_size(mock_metrics)

        assert result == 20.0  # (10 + 20 + 30) / 3

    @pytest.mark.metrics
    def test_average_size_empty_sizes(self):
        """Test average with empty sizes raises ZeroDivisionError."""
        mock_metrics = Mock()
        mock_metrics.sizes = Counter()

        with pytest.raises(ZeroDivisionError):
            average_size(mock_metrics)

    @pytest.mark.metrics
    def test_average_size_single_item(self):
        """Test average with single item."""
        mock_metrics = Mock()
        mock_metrics.sizes = Counter({"item": 42})

        result = average_size(mock_metrics)

        assert result == 42.0

    @pytest.mark.metrics
    def test_average_size_none_sizes_raises_error(self):
        """Test that None sizes raises TypeError."""
        mock_metrics = Mock()
        mock_metrics.sizes = None

        with pytest.raises(TypeError):
            average_size(mock_metrics)


class TestNewBookmarksByDate:
    """Tests for the new_bookmarks_by_date function."""

    @pytest.mark.metrics
    def test_new_bookmarks_by_date_basic(self):
        """Test basic date grouping functionality."""
        mock_metrics = Mock()
        mock_metrics.bookmarks.added = {
            1641859200,  # 2022-01-11 00:00:00 UTC
            1641945600,  # 2022-01-12 00:00:00 UTC
            1641945700,  # 2022-01-12 00:01:40 UTC  (same day)
            1642032000,  # 2022-01-13 00:00:00 UTC
        }

        result = new_bookmarks_by_date(mock_metrics)

        assert "2022-01-11" in result
        assert "2022-01-12" in result
        assert "2022-01-13" in result

        assert len(result["2022-01-11"]) == 1
        assert len(result["2022-01-12"]) == 2
        assert len(result["2022-01-13"]) == 1

        assert 1641859200 in result["2022-01-11"]
        assert 1641945600 in result["2022-01-12"]
        assert 1641945700 in result["2022-01-12"]
        assert 1642032000 in result["2022-01-13"]

    @pytest.mark.metrics
    def test_new_bookmarks_by_date_empty_added(self):
        """Test with no new bookmarks."""
        mock_metrics = Mock()
        mock_metrics.bookmarks.added = set()

        result = new_bookmarks_by_date(mock_metrics)

        assert result == {}

    @pytest.mark.metrics
    def test_new_bookmarks_by_date_sorts_within_day(self):
        """Test that bookmarks within a day are sorted."""
        mock_metrics = Mock()
        mock_metrics.bookmarks.added = {
            1641945700,  # Later timestamp
            1641945600,  # Earlier timestamp (same day)
        }

        result = new_bookmarks_by_date(mock_metrics)

        # Should be sorted within the day
        assert result["2022-01-12"] == [1641945600, 1641945700]


class TestTagsUsageByDate:
    """Tests for the tags_usage_by_date function."""

    @pytest.mark.metrics
    def test_tags_usage_by_date_basic(self):
        """Test basic tag usage grouping by date."""
        mock_bookmark1 = Mock()
        mock_bookmark1.created = 1641859200  # 2022-01-11
        mock_bookmark1.tags = ["python", "web"]

        mock_bookmark2 = Mock()
        mock_bookmark2.created = 1641945600  # 2022-01-12
        mock_bookmark2.tags = ["python", "testing"]

        mock_bookmark3 = Mock()
        # 2022-01-12 (same day as bookmark2)
        mock_bookmark3.created = 1641945700
        mock_bookmark3.tags = ["python"]

        mock_metrics = Mock()
        mock_metrics.bookmarks.new_bookmarks = [
            mock_bookmark1, mock_bookmark2, mock_bookmark3]

        result = tags_usage_by_date(mock_metrics)

        assert "2022-01-11" in result
        assert "2022-01-12" in result

        # Day 1: python(1), web(1)
        assert result["2022-01-11"]["python"] == 1
        assert result["2022-01-11"]["web"] == 1
        assert "testing" not in result["2022-01-11"]

        # Day 2: python(2), testing(1)
        assert result["2022-01-12"]["python"] == 2
        assert result["2022-01-12"]["testing"] == 1
        assert "web" not in result["2022-01-12"]

    @pytest.mark.metrics
    def test_tags_usage_by_date_empty_bookmarks(self):
        """Test with no new bookmarks."""
        mock_metrics = Mock()
        mock_metrics.bookmarks.new_bookmarks = []

        result = tags_usage_by_date(mock_metrics)

        assert result == {}

    @pytest.mark.metrics
    def test_tags_usage_by_date_bookmarks_without_tags(self):
        """Test with bookmarks that have no tags."""
        mock_bookmark = Mock()
        mock_bookmark.created = 1641859200  # 2022-01-11
        mock_bookmark.tags = []

        mock_metrics = Mock()
        mock_metrics.bookmarks.new_bookmarks = [mock_bookmark]

        result = tags_usage_by_date(mock_metrics)

        assert "2022-01-11" in result
        assert len(result["2022-01-11"]) == 0  # Empty Counter


class TestAllBookmarksSorted:
    """Tests for the all_bookmarks_sorted function."""

    @pytest.mark.metrics
    def test_all_bookmarks_sorted_basic(self):
        """Test basic bookmark collection and sorting."""
        # Create mock bookmarks with different creation times
        bookmark1 = Mock()
        bookmark1.created = 1641945600

        bookmark2 = Mock()
        bookmark2.created = 1641859200  # Earlier

        bookmark3 = Mock()
        bookmark3.created = 1642032000  # Latest

        # Create mock folder structure
        subfolder = Mock()
        subfolder.content = [bookmark3]

        root_folder = Mock()
        root_folder.content = [bookmark1, bookmark2, subfolder]

        with patch('bookmarkos.metrics.isinstance') as mock_isinstance:
            # Configure isinstance to identify bookmarks vs folders
            def isinstance_side_effect(obj, cls):
                if cls.__name__ == 'Bookmark':
                    return obj in [bookmark1, bookmark2, bookmark3]
                elif cls.__name__ == 'Folder':
                    return obj == subfolder
                return False

            mock_isinstance.side_effect = isinstance_side_effect

            result = all_bookmarks_sorted(root_folder)

            # Should return bookmarks sorted by creation time
            assert len(result) == 3
            assert result[0] == bookmark2  # Earliest (1641859200)
            assert result[1] == bookmark1  # Middle (1641945600)
            assert result[2] == bookmark3  # Latest (1642032000)

    @pytest.mark.metrics
    def test_all_bookmarks_sorted_empty_folder(self):
        """Test with empty folder."""
        root_folder = Mock()
        root_folder.content = []

        result = all_bookmarks_sorted(root_folder)

        assert result == []

    @pytest.mark.metrics
    def test_all_bookmarks_sorted_nested_structure(self):
        """Test with deeply nested folder structure."""
        bookmark1 = Mock()
        bookmark1.created = 100

        bookmark2 = Mock()
        bookmark2.created = 200

        bookmark3 = Mock()
        bookmark3.created = 50

        # Deep nesting: root -> folder1 -> folder2 -> bookmark3
        deep_folder = Mock()
        deep_folder.content = [bookmark3]

        mid_folder = Mock()
        mid_folder.content = [bookmark2, deep_folder]

        root_folder = Mock()
        root_folder.content = [bookmark1, mid_folder]

        with patch('bookmarkos.metrics.isinstance') as mock_isinstance:
            def isinstance_side_effect(obj, cls):
                if cls.__name__ == 'Bookmark':
                    return obj in [bookmark1, bookmark2, bookmark3]
                elif cls.__name__ == 'Folder':
                    return obj in [mid_folder, deep_folder]
                return False

            mock_isinstance.side_effect = isinstance_side_effect

            result = all_bookmarks_sorted(root_folder)

            # Should collect all bookmarks and sort by creation time
            assert len(result) == 3
            assert result[0] == bookmark3  # created: 50
            assert result[1] == bookmark1  # created: 100
            assert result[2] == bookmark2  # created: 200


class TestDifferentiateMetrics:
    """Tests for the differentiate_metrics function."""

    @pytest.mark.metrics
    def test_differentiate_metrics_with_previous(self):
        """Test differentiate_metrics with previous metrics for comparison."""
        # Mock current week data with proper content
        mock_this_week = Mock()
        mock_this_week.content = []  # Empty list for now, could add mock bookmarks

        # Mock current metrics
        mock_these = Mock()
        mock_these.bookmarks = Mock()
        mock_these.bookmarks.count = 150
        mock_these.bookmarks.items = {1, 2, 3, 4, 5}

        mock_these.folders = Mock()
        mock_these.folders.count = 10
        mock_these.folders.items = {"f1", "f2", "f3"}

        mock_these.tags = Mock()
        mock_these.tags.items = {"python", "web", "api"}

        # Mock previous metrics
        mock_those = Mock()
        mock_those.bookmarks = Mock()
        mock_those.bookmarks.count = 140
        mock_those.bookmarks.items = {1, 2, 3}

        mock_those.folders = Mock()
        mock_those.folders.count = 9
        mock_those.folders.items = {"f1", "f2"}

        mock_those.tags = Mock()
        mock_those.tags.items = {"python", "web"}

        # Mock all_bookmarks_sorted to return bookmark objects for IDs 4 and 5
        mock_bookmark_4 = Mock()
        mock_bookmark_4.created = 1640995200  # 2022-01-01 timestamp
        mock_bookmark_5 = Mock()
        mock_bookmark_5.created = 1641081600  # 2022-01-02 timestamp

        with patch('bookmarkos.metrics.all_bookmarks_sorted') as mock_sorted:
            # Return bookmarks sorted by creation time
            mock_sorted.return_value = [mock_bookmark_4, mock_bookmark_5]

            with patch('bookmarkos.metrics.new_bookmarks_by_date') as mock_by_date, \
                    patch('bookmarkos.metrics.tags_usage_by_date') as mock_tags_by_date:
                mock_by_date.return_value = {}
                mock_tags_by_date.return_value = {}

                differentiate_metrics(mock_this_week, mock_these, mock_those)

            # Check bookmarks delta calculations
            assert mock_these.bookmarks.delta == 10  # 150 - 140
        assert mock_these.bookmarks.delta_pct == pytest.approx(10/140)
        assert mock_these.bookmarks.added == {4, 5}
        assert mock_these.bookmarks.added_count == 2
        assert mock_these.bookmarks.deleted == set()
        assert mock_these.bookmarks.deleted_count == 0

        # Check folders delta calculations
        assert mock_these.folders.delta == 1  # 10 - 9
        assert mock_these.folders.delta_pct == pytest.approx(1/9)
        assert mock_these.folders.added == {"f3"}
        assert mock_these.folders.added_count == 1

        # Check tags delta calculations
        assert mock_these.tags.delta == 1  # 3 - 2
        assert mock_these.tags.delta_pct == pytest.approx(1/2)
        assert mock_these.tags.added == {"api"}
        assert mock_these.tags.added_count == 1

    @pytest.mark.metrics
    def test_differentiate_metrics_initial_data(self):
        """Test differentiate_metrics with no previous data (initial state)."""
        mock_this_week = Mock()
        mock_this_week.content = []  # Need proper content for all_bookmarks_sorted

        mock_these = Mock()
        mock_these.bookmarks = Mock()
        mock_these.bookmarks.count = 100
        mock_these.bookmarks.items = {1, 2, 3}

        mock_these.folders = Mock()
        mock_these.folders.count = 5
        mock_these.folders.items = {"f1", "f2"}

        mock_these.tags = Mock()
        mock_these.tags.items = {"python", "web"}

        # Mock all_bookmarks_sorted to return bookmark objects for IDs 1, 2, 3
        mock_bookmark_1 = Mock()
        mock_bookmark_1.created = 1640995200  # 2022-01-01 timestamp
        mock_bookmark_2 = Mock()
        mock_bookmark_2.created = 1641081600  # 2022-01-02 timestamp
        mock_bookmark_3 = Mock()
        mock_bookmark_3.created = 1641168000  # 2022-01-03 timestamp

        with patch('bookmarkos.metrics.all_bookmarks_sorted') as mock_sorted:
            # Return bookmarks sorted by creation time
            mock_sorted.return_value = [
                mock_bookmark_1, mock_bookmark_2, mock_bookmark_3]

            with patch('bookmarkos.metrics.new_bookmarks_by_date') as mock_by_date, \
                    patch('bookmarkos.metrics.tags_usage_by_date') as mock_tags_by_date:
                mock_by_date.return_value = {}
                mock_tags_by_date.return_value = {}

                differentiate_metrics(mock_this_week, mock_these, None)

        # For initial data, delta should equal count
        assert mock_these.bookmarks.delta == 100
        assert mock_these.bookmarks.delta_pct == 1.0
        assert mock_these.bookmarks.added == {1, 2, 3}
        assert mock_these.bookmarks.added_count == 100
        assert mock_these.bookmarks.deleted == set()
        assert mock_these.bookmarks.deleted_count == 0

        assert mock_these.folders.delta == 5
        assert mock_these.folders.delta_pct == 1.0

        assert mock_these.tags.delta == 2
        assert mock_these.tags.delta_pct == 1.0

    @pytest.mark.metrics
    def test_differentiate_metrics_zero_division_handling(self):
        """Test handling of division by zero in delta calculations."""
        mock_this_week = Mock()
        mock_this_week.content = []  # Need proper content for all_bookmarks_sorted

        mock_these = Mock()
        mock_these.bookmarks = Mock()
        mock_these.bookmarks.count = 50
        mock_these.bookmarks.items = {1, 2}

        mock_these.folders = Mock()
        mock_these.folders.count = 0  # Zero current folders
        mock_these.folders.items = set()

        mock_these.tags = Mock()
        mock_these.tags.items = set()

        # Previous metrics with zero counts
        mock_those = Mock()
        mock_those.bookmarks = Mock()
        mock_those.bookmarks.count = 0  # Zero previous bookmarks
        mock_those.bookmarks.items = set()

        mock_those.folders = Mock()
        mock_those.folders.count = 5
        mock_those.folders.items = {"f1"}

        mock_those.tags = Mock()
        mock_those.tags.items = set()

        # Mock all_bookmarks_sorted to return bookmark objects for IDs 1, 2
        mock_bookmark_1 = Mock()
        mock_bookmark_1.created = 1640995200  # 2022-01-01 timestamp
        mock_bookmark_2 = Mock()
        mock_bookmark_2.created = 1641081600  # 2022-01-02 timestamp

        with patch('bookmarkos.metrics.all_bookmarks_sorted') as mock_sorted:
            # Return bookmarks sorted by creation time
            mock_sorted.return_value = [mock_bookmark_1, mock_bookmark_2]

            with patch('bookmarkos.metrics.new_bookmarks_by_date') as mock_by_date, \
                    patch('bookmarkos.metrics.tags_usage_by_date') as mock_tags_by_date:
                mock_by_date.return_value = {}
                mock_tags_by_date.return_value = {}

                differentiate_metrics(mock_this_week, mock_these, mock_those)

        # Division by zero should be handled
        assert mock_these.bookmarks.delta_pct == 1.0  # Special case for zero base
        # 0-5)/5 = -1
        assert mock_these.folders.delta_pct == pytest.approx(-1.0)
        assert mock_these.tags.delta_pct == 0.0  # Both zero


class TestGatherMetrics:
    """Tests for the gather_metrics function."""

    @pytest.mark.metrics
    def test_gather_metrics_basic(self):
        """Test basic metrics gathering."""
        # Create mock folder with string name attribute
        mock_week = Mock()
        mock_week.name = ""  # Root folder has empty name

        with patch('bookmarkos.metrics._gather_metrics') as mock_gather, \
                patch('bookmarkos.metrics.Metrics') as MockMetrics, \
                patch('bookmarkos.metrics.average_size') as mock_avg, \
                patch('bookmarkos.metrics.get_largest_and_smallest') as mock_largest, \
                patch('bookmarkos.metrics.isinstance') as mock_isinstance:

            # Setup mocks
            mock_metrics = Mock()
            MockMetrics.return_value = mock_metrics

            mock_gather.return_value = Counter({"folder1": 5, "folder2": 3})
            mock_avg.return_value = 4.0
            mock_largest.return_value = (
                [(1, 5, ["folder1"])], [(2, 3, ["folder2"])])

            mock_metrics.tags.items = {"python", "web"}
            mock_metrics.tags.sizes = Counter({"python": 10, "web": 5})
            mock_metrics.folders = Mock()

            # Mock isinstance to return False for all checks (no subfolders or bookmarks)
            mock_isinstance.return_value = False

            # Mock folder content to be empty
            mock_week.content = []

            result = gather_metrics(mock_week)

            # Verify _gather_metrics was called
            mock_gather.assert_called_once_with(mock_week, [''], mock_metrics)

            # Verify averages were calculated
            assert mock_avg.call_count == 2  # Called for tags and folders

            # Verify unique tags count was set
            assert mock_metrics.tags.unique_tags_count == 2

            # Verify top/bottom calculations
            assert mock_largest.call_count == 2  # Called for folders and tags

            assert result == mock_metrics


class TestMetricsIntegration:
    """Integration tests for metrics calculations."""

    @pytest.mark.integration
    @pytest.mark.metrics
    def test_metrics_integration_realistic_scenario(self):
        """Test metrics with a realistic bookmark structure."""
        # Create mock realistic folder structure
        mock_root = Mock()
        mock_root.name = ""  # Root folder name
        mock_root.content = []

        # Mock the Metrics creation to avoid the empty sizes issue
        with patch('bookmarkos.metrics.Metrics') as MockMetrics, \
                patch('bookmarkos.metrics.average_size') as mock_avg, \
                patch('bookmarkos.metrics._gather_metrics'):

            mock_metrics = Mock()
            MockMetrics.return_value = mock_metrics
            mock_metrics.tags.items = set()  # Empty set to avoid ZeroDivisionError
            mock_avg.side_effect = ZeroDivisionError()  # Expected with empty data

            try:
                gather_metrics(mock_root)
                # Should not get here if average_size raises ZeroDivisionError
                pytest.fail("Expected ZeroDivisionError from empty metrics")
            except ZeroDivisionError:
                # This is expected behavior with empty data
                pass
