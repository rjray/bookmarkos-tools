# pylint: disable=missing-function-docstring, missing-class-docstring, invalid-name, no-member, import-error, line-too-long

"""Unit tests for bookmarkos.data.metrics module."""

from collections import Counter
from unittest.mock import Mock
from bookmarkos.data.metrics import (
    CoreMetrics, SizeMetrics, FoldersMetrics,
    BookmarksMetrics, TagsMetrics, Metrics, SizeRankedList
)


class TestCoreMetrics:
    """Tests for the CoreMetrics class."""

    def test_core_metrics_creation_with_defaults(self):
        """Test CoreMetrics creation with default values."""
        metrics = CoreMetrics()

        assert metrics.count == 0
        assert metrics.items == set()
        assert metrics.added == set()
        assert metrics.added_count == 0
        assert metrics.deleted == set()
        assert metrics.deleted_count == 0
        assert metrics.delta == 0
        assert metrics.delta_pct == 0.0

    def test_core_metrics_creation_with_values(self):
        """Test CoreMetrics creation with specified values."""
        items = {"item1", "item2", "item3"}
        added = {"item3"}
        deleted = {"item0"}

        metrics = CoreMetrics(
            count=3,
            items=items,
            added=added,
            added_count=1,
            deleted=deleted,
            deleted_count=1,
            delta=0,
            delta_pct=0.0
        )

        assert metrics.count == 3
        assert metrics.items == items
        assert metrics.added == added
        assert metrics.added_count == 1
        assert metrics.deleted == deleted
        assert metrics.deleted_count == 1
        assert metrics.delta == 0
        assert metrics.delta_pct == 0.0

    def test_core_metrics_sets_are_mutable(self):
        """Test that sets in CoreMetrics can be modified."""
        metrics = CoreMetrics()

        metrics.items.add("new_item")
        metrics.added.add("added_item")
        metrics.deleted.add("deleted_item")

        assert "new_item" in metrics.items
        assert "added_item" in metrics.added
        assert "deleted_item" in metrics.deleted


class TestSizeMetrics:
    """Tests for the SizeMetrics class."""

    def test_size_metrics_creation_with_defaults(self):
        """Test SizeMetrics creation with default values."""
        metrics = SizeMetrics()

        assert isinstance(metrics.sizes, Counter)
        assert len(metrics.sizes) == 0
        assert metrics.min_size > 0  # sys.maxsize
        assert metrics.max_size == 0
        assert metrics.avg_size == 0.0
        assert metrics.top_n == []
        assert metrics.bottom_n == []

    def test_size_metrics_creation_with_values(self):
        """Test SizeMetrics creation with specified values."""
        sizes = Counter({"folder1": 5, "folder2": 3, "folder3": 8})
        top_n = [(1, 8, ["folder3"]), (2, 5, ["folder1"])]
        bottom_n = [(3, 3, ["folder2"])]

        metrics = SizeMetrics(
            sizes=sizes,
            min_size=3,
            max_size=8,
            avg_size=5.33,
            top_n=top_n,
            bottom_n=bottom_n
        )

        assert metrics.sizes == sizes
        assert metrics.min_size == 3
        assert metrics.max_size == 8
        assert metrics.avg_size == 5.33
        assert metrics.top_n == top_n
        assert metrics.bottom_n == bottom_n

    def test_size_metrics_counter_operations(self):
        """Test Counter operations on sizes."""
        metrics = SizeMetrics()

        metrics.sizes["folder1"] = 5
        metrics.sizes["folder2"] = 3
        metrics.sizes.update({"folder3": 8})

        assert metrics.sizes["folder1"] == 5
        assert metrics.sizes["folder2"] == 3
        assert metrics.sizes["folder3"] == 8
        assert metrics.sizes.most_common(1) == [("folder3", 8)]

    def test_size_ranked_list_structure(self):
        """Test SizeRankedList type structure."""
        # Test that SizeRankedList can hold the expected tuple structure
        ranked_list: SizeRankedList = [
            (1, 10, ["item1"]),
            (2, 8, ["item2", "item3"]),  # Tie at rank 2
            (4, 5, ["item4"])
        ]

        assert len(ranked_list) == 3
        assert ranked_list[0] == (1, 10, ["item1"])
        assert ranked_list[1] == (2, 8, ["item2", "item3"])
        assert ranked_list[2] == (4, 5, ["item4"])


class TestFoldersMetrics:
    """Tests for the FoldersMetrics class."""

    def test_folders_metrics_inherits_from_core_and_size(self):
        """Test that FoldersMetrics inherits from both CoreMetrics and SizeMetrics."""
        metrics = FoldersMetrics()

        # CoreMetrics attributes
        assert hasattr(metrics, 'count')
        assert hasattr(metrics, 'items')
        assert hasattr(metrics, 'delta')

        # SizeMetrics attributes
        assert hasattr(metrics, 'sizes')
        assert hasattr(metrics, 'min_size')
        assert hasattr(metrics, 'max_size')
        assert hasattr(metrics, 'avg_size')

        # FoldersMetrics specific attributes
        assert hasattr(metrics, 'max_depth')

    def test_folders_metrics_creation_with_defaults(self):
        """Test FoldersMetrics creation with default values."""
        metrics = FoldersMetrics()

        assert metrics.count == 0
        assert metrics.items == set()
        assert isinstance(metrics.sizes, Counter)
        assert metrics.max_depth == 0

    def test_folders_metrics_creation_with_values(self):
        """Test FoldersMetrics creation with specified values."""
        metrics = FoldersMetrics(
            count=5,
            max_depth=3,
            min_size=1,
            max_size=10
        )

        assert metrics.count == 5
        assert metrics.max_depth == 3
        assert metrics.min_size == 1
        assert metrics.max_size == 10


class TestBookmarksMetrics:
    """Tests for the BookmarksMetrics class."""

    def test_bookmarks_metrics_inherits_from_core(self):
        """Test that BookmarksMetrics inherits from CoreMetrics."""
        metrics = BookmarksMetrics()

        # CoreMetrics attributes
        assert hasattr(metrics, 'count')
        assert hasattr(metrics, 'items')
        assert hasattr(metrics, 'delta')

        # BookmarksMetrics specific attributes
        assert hasattr(metrics, 'new_bookmarks')
        assert hasattr(metrics, 'new_bookmarks_by_date')

    def test_bookmarks_metrics_creation_with_defaults(self):
        """Test BookmarksMetrics creation with default values."""
        metrics = BookmarksMetrics()

        assert metrics.count == 0
        assert metrics.items == set()
        assert metrics.new_bookmarks == []
        assert metrics.new_bookmarks_by_date == {}

    def test_bookmarks_metrics_new_bookmarks_list(self):
        """Test new_bookmarks list operations."""
        metrics = BookmarksMetrics()

        # Mock bookmark objects
        bookmark1 = Mock()
        bookmark1.name = "Bookmark 1"
        bookmark2 = Mock()
        bookmark2.name = "Bookmark 2"

        metrics.new_bookmarks.append(bookmark1)
        metrics.new_bookmarks.append(bookmark2)

        assert len(metrics.new_bookmarks) == 2
        assert metrics.new_bookmarks[0].name == "Bookmark 1"
        assert metrics.new_bookmarks[1].name == "Bookmark 2"

    def test_bookmarks_metrics_by_date_dict(self):
        """Test new_bookmarks_by_date dictionary operations."""
        metrics = BookmarksMetrics()

        metrics.new_bookmarks_by_date["2022-01-01"] = [1641859200, 1641862800]
        metrics.new_bookmarks_by_date["2022-01-02"] = [1641945600]

        assert len(metrics.new_bookmarks_by_date) == 2
        assert metrics.new_bookmarks_by_date["2022-01-01"] == [
            1641859200, 1641862800]
        assert metrics.new_bookmarks_by_date["2022-01-02"] == [1641945600]


class TestTagsMetrics:
    """Tests for the TagsMetrics class."""

    def test_tags_metrics_inherits_from_core_and_size(self):
        """Test that TagsMetrics inherits from both CoreMetrics and SizeMetrics."""
        metrics = TagsMetrics()

        # CoreMetrics attributes
        assert hasattr(metrics, 'count')
        assert hasattr(metrics, 'items')
        assert hasattr(metrics, 'delta')

        # SizeMetrics attributes
        assert hasattr(metrics, 'sizes')
        assert hasattr(metrics, 'min_size')
        assert hasattr(metrics, 'max_size')

        # TagsMetrics specific attributes
        assert hasattr(metrics, 'unique_tags_count')
        assert hasattr(metrics, 'tags_by_date')

    def test_tags_metrics_creation_with_defaults(self):
        """Test TagsMetrics creation with default values."""
        metrics = TagsMetrics()

        assert metrics.count == 0
        assert metrics.items == set()
        assert isinstance(metrics.sizes, Counter)
        assert metrics.unique_tags_count == 0
        assert metrics.tags_by_date == {}

    def test_tags_metrics_creation_with_values(self):
        """Test TagsMetrics creation with specified values."""
        tags_set = {"python", "web", "api"}
        sizes = Counter({"python": 10, "web": 5, "api": 3})

        metrics = TagsMetrics(
            count=18,  # Total tag usage count
            items=tags_set,
            sizes=sizes,
            unique_tags_count=3
        )

        assert metrics.count == 18
        assert metrics.items == tags_set
        assert metrics.sizes == sizes
        assert metrics.unique_tags_count == 3

    def test_tags_by_date_counter_operations(self):
        """Test tags_by_date with Counter operations."""
        metrics = TagsMetrics()

        # Add tag counts for specific dates
        metrics.tags_by_date["2022-01-01"] = Counter({"python": 3, "web": 2})
        metrics.tags_by_date["2022-01-02"] = Counter({"python": 1, "api": 2})

        assert metrics.tags_by_date["2022-01-01"]["python"] == 3
        assert metrics.tags_by_date["2022-01-01"]["web"] == 2
        assert metrics.tags_by_date["2022-01-02"]["python"] == 1
        assert metrics.tags_by_date["2022-01-02"]["api"] == 2

    def test_unique_tags_vs_total_count(self):
        """Test relationship between unique_tags_count and total count."""
        metrics = TagsMetrics()

        # Set up scenario: 3 unique tags, but total usage count is higher
        metrics.items = {"python", "web", "api"}
        metrics.unique_tags_count = 3
        metrics.count = 15  # Total usage across all bookmarks
        metrics.sizes = Counter({"python": 8, "web": 4, "api": 3})

        assert metrics.unique_tags_count == 3
        assert metrics.count == 15
        assert sum(metrics.sizes.values()) == 15


class TestMetrics:
    """Tests for the main Metrics class."""

    def test_metrics_creation_with_defaults(self):
        """Test Metrics creation with default values."""
        metrics = Metrics()

        assert isinstance(metrics.folders, FoldersMetrics)
        assert isinstance(metrics.bookmarks, BookmarksMetrics)
        assert isinstance(metrics.tags, TagsMetrics)

        # Check that sub-metrics have default values
        assert metrics.folders.count == 0
        assert metrics.bookmarks.count == 0
        assert metrics.tags.count == 0

    def test_metrics_creation_with_custom_submetrics(self):
        """Test Metrics creation with custom sub-metrics."""
        folders = FoldersMetrics(count=5, max_depth=3)
        bookmarks = BookmarksMetrics(count=20)
        tags = TagsMetrics(count=45, unique_tags_count=15)

        metrics = Metrics(
            folders=folders,
            bookmarks=bookmarks,
            tags=tags
        )

        assert metrics.folders.count == 5
        assert metrics.folders.max_depth == 3
        assert metrics.bookmarks.count == 20
        assert metrics.tags.count == 45
        assert metrics.tags.unique_tags_count == 15

    def test_metrics_sub_objects_are_independent(self):
        """Test that sub-metrics objects are independent."""
        metrics = Metrics()

        # Modify one sub-metric
        metrics.folders.count = 10
        metrics.bookmarks.count = 20

        # Other sub-metrics should be unaffected
        assert metrics.folders.count == 10
        assert metrics.bookmarks.count == 20
        assert metrics.tags.count == 0  # Still default

    def test_metrics_complex_scenario(self):
        """Test a complex realistic metrics scenario."""
        metrics = Metrics()

        # Set up folders
        metrics.folders.count = 8
        metrics.folders.max_depth = 4
        metrics.folders.items = {f"folder_{i}" for i in range(8)}
        metrics.folders.sizes = Counter({
            "folder_0": 15, "folder_1": 8, "folder_2": 3,
            "folder_3": 12, "folder_4": 1, "folder_5": 6,
            "folder_6": 9, "folder_7": 4
        })

        # Set up bookmarks
        metrics.bookmarks.count = 58
        metrics.bookmarks.items = {1641921698 + i for i in range(58)}
        metrics.bookmarks.added = {1641921698 + i for i in range(5)}
        metrics.bookmarks.added_count = 5

        # Set up tags
        metrics.tags.count = 125  # Total usage
        metrics.tags.unique_tags_count = 35  # Unique tags
        metrics.tags.items = {f"tag_{i}" for i in range(35)}
        metrics.tags.sizes = Counter({
            "python": 15, "web": 12, "api": 8, "javascript": 7,
            "react": 6, "nodejs": 5, "database": 4
        })

        # Verify the setup
        assert metrics.folders.count == 8
        assert metrics.bookmarks.count == 58
        assert metrics.tags.count == 125
        assert metrics.tags.unique_tags_count == 35
        assert len(metrics.bookmarks.added) == 5
        assert metrics.folders.sizes["folder_0"] == 15


class TestMetricsDataclassFeatures:
    """Tests for dataclass-specific features of metrics classes."""

    def test_metrics_equality(self):
        """Test equality comparison of metrics objects."""
        metrics1 = Metrics()
        metrics2 = Metrics()

        assert metrics1 == metrics2

        # Modify one and test inequality
        metrics1.folders.count = 5
        assert metrics1 != metrics2

    def test_core_metrics_equality(self):
        """Test equality comparison of CoreMetrics objects."""
        metrics1 = CoreMetrics(count=5, delta=2)
        metrics2 = CoreMetrics(count=5, delta=2)
        metrics3 = CoreMetrics(count=3, delta=2)

        assert metrics1 == metrics2
        assert metrics1 != metrics3

    def test_metrics_repr(self):
        """Test string representation of metrics objects."""
        metrics = CoreMetrics(count=5, delta=2)
        repr_str = repr(metrics)

        assert "CoreMetrics" in repr_str
        assert "count=5" in repr_str
        assert "delta=2" in repr_str

    def test_size_metrics_excluded_fields_in_comparison(self):
        """Test that top_n and bottom_n are excluded from comparison."""
        metrics1 = SizeMetrics(min_size=1, max_size=10)
        metrics2 = SizeMetrics(min_size=1, max_size=10)

        # Should be equal even with different top_n/bottom_n
        metrics1.top_n = [(1, 10, ["item1"])]
        metrics2.top_n = [(1, 8, ["item2"])]

        assert metrics1 == metrics2  # top_n excluded from comparison
