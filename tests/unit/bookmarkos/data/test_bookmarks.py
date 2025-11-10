# pylint: disable=missing-function-docstring, missing-class-docstring, invalid-name, no-member, import-error, line-too-long

"""Unit tests for bookmarkos.data.bookmarks module."""

from bookmarkos.data.bookmarks import Node, Folder, Bookmark, parse_fragment

import pytest


class TestNode:
    """Tests for the Node base class."""

    def test_node_creation_with_defaults(self):
        """Test Node creation with default values."""
        node = Node()

        assert node.name == ''
        assert node.created == 0
        assert node.updated == 0
        assert node.parent == []

    def test_node_creation_with_values(self):
        """Test Node creation with specified values."""
        node = Node(
            name="Test Node",
            created=1641921698,
            updated=1641921700,
            parent=["root", "folder1"]
        )

        assert node.name == "Test Node"
        assert node.created == 1641921698
        assert node.updated == 1641921700
        assert node.parent == ["root", "folder1"]

    def test_node_parent_list_is_mutable(self):
        """Test that parent list can be modified."""
        node = Node()
        node.parent.append("new_folder")

        assert node.parent == ["new_folder"]


class TestFolder:
    """Tests for the Folder class."""

    def test_folder_creation_with_defaults(self):
        """Test Folder creation with default values."""
        folder = Folder()

        assert folder.name == ''
        assert folder.created == 0
        assert folder.updated == 0
        assert folder.parent == []
        assert folder.depth == 0
        assert folder.content == []

    def test_folder_creation_with_values(self):
        """Test Folder creation with specified values."""
        bookmark = Bookmark(name="Test Bookmark", url="https://example.com")
        subfolder = Folder(name="Subfolder")

        folder = Folder(
            name="Main Folder",
            created=1641921698,
            updated=1641921700,
            parent=["root"],
            depth=1,
            content=[bookmark, subfolder]
        )

        assert folder.name == "Main Folder"
        assert folder.created == 1641921698
        assert folder.updated == 1641921700
        assert folder.parent == ["root"]
        assert folder.depth == 1
        assert len(folder.content) == 2
        assert isinstance(folder.content[0], Bookmark)
        assert isinstance(folder.content[1], Folder)

    def test_folder_content_is_mutable(self):
        """Test that folder content can be modified."""
        folder = Folder()
        bookmark = Bookmark(name="Test", url="https://test.com")

        folder.content.append(bookmark)

        assert len(folder.content) == 1
        assert folder.content[0] is bookmark

    def test_folder_fill_empty_markup(self):
        """Test fill method with empty markup."""
        folder = Folder()
        result = folder.fill("")

        assert result is folder  # Returns self
        assert folder.name == ''
        assert folder.created == 0
        assert folder.updated == 0

    def test_folder_fill_valid_markup(self):
        """Test fill method with valid H3 markup."""
        folder = Folder()
        markup = '<H3 ADD_DATE="1641921698" LAST_MODIFIED="1641921700">Test Folder</H3>'

        result = folder.fill(markup)

        assert result is folder  # Returns self
        assert folder.name == "Test Folder"
        assert folder.created == 1641921698
        assert folder.updated == 1641921700

    @pytest.mark.parser
    def test_folder_fill_minimal_markup(self):
        """Test fill method with minimal required attributes."""
        folder = Folder()
        markup = '<H3 ADD_DATE="1234567890" LAST_MODIFIED="1234567891">Minimal</H3>'

        folder.fill(markup)

        assert folder.name == "Minimal"
        assert folder.created == 1234567890
        assert folder.updated == 1234567891


class TestBookmark:
    """Tests for the Bookmark class."""

    def test_bookmark_creation_with_defaults(self):
        """Test Bookmark creation with default values."""
        bookmark = Bookmark()

        assert bookmark.name == ''
        assert bookmark.created == 0
        assert bookmark.updated == 0
        assert bookmark.parent == []
        assert bookmark.url == ''
        assert bookmark.visited is None
        assert bookmark.tags == []
        assert bookmark.notes is None

    def test_bookmark_creation_with_values(self):
        """Test Bookmark creation with specified values."""
        bookmark = Bookmark(
            name="Test Bookmark",
            url="https://example.com",
            created=1641921698,
            updated=1641921700,
            visited=1641921699,
            tags=["python", "testing"],
            notes="Test notes",
            parent=["root", "dev"]
        )

        assert bookmark.name == "Test Bookmark"
        assert bookmark.url == "https://example.com"
        assert bookmark.created == 1641921698
        assert bookmark.updated == 1641921700
        assert bookmark.visited == 1641921699
        assert bookmark.tags == ["python", "testing"]
        assert bookmark.notes == "Test notes"
        assert bookmark.parent == ["root", "dev"]

    def test_bookmark_tags_is_mutable(self):
        """Test that bookmark tags can be modified."""
        bookmark = Bookmark()
        bookmark.tags.append("new_tag")

        assert bookmark.tags == ["new_tag"]

    def test_bookmark_fill_basic_markup(self):
        """Test filling bookmark with basic markup."""
        markup = '<A HREF="https://example.com" ADD_DATE="1641921698" LAST_MODIFIED="1641921698">Example Site</A>'
        bookmark = Bookmark()

        result = bookmark.fill(markup)

        assert result is bookmark  # Should return self
        assert bookmark.name == "Example Site"
        assert bookmark.url == "https://example.com"
        assert bookmark.created == 1641921698
        assert bookmark.updated == 1641921698
        assert bookmark.visited is None
        assert bookmark.tags == [""]  # Empty TAGS attr splits to [""]

    def test_bookmark_fill_with_visit_and_tags(self):
        """Test fill method with visit time and tags."""
        bookmark = Bookmark()
        markup = '<A HREF="https://test.com" ADD_DATE="1641921698" LAST_MODIFIED="1641921700" LAST_VISIT="1641921699" TAGS="python, testing, web">Test Site</A>'

        bookmark.fill(markup)

        assert bookmark.name == "Test Site"
        assert bookmark.url == "https://test.com"
        assert bookmark.created == 1641921698
        assert bookmark.updated == 1641921700
        assert bookmark.visited == 1641921699
        assert bookmark.tags == ["python", "testing", "web"]

    def test_bookmark_fill_empty_tags(self):
        """Test fill method with empty tags attribute."""
        bookmark = Bookmark()
        markup = '<A HREF="https://test.com" ADD_DATE="1641921698" LAST_MODIFIED="1641921700" TAGS="">Test</A>'

        bookmark.fill(markup)

        assert bookmark.tags == [""]  # Empty string splits to [""]

    def test_bookmark_fill_single_tag(self):
        """Test fill method with single tag."""
        bookmark = Bookmark()
        markup = '<A HREF="https://test.com" ADD_DATE="1641921698" LAST_MODIFIED="1641921700" TAGS="python">Test</A>'

        bookmark.fill(markup)

        assert bookmark.tags == ["python"]

    @pytest.mark.parser
    def test_bookmark_fill_tags_with_spaces(self):
        """Test fill method with tags containing spaces."""
        bookmark = Bookmark()
        markup = '<A HREF="https://test.com" ADD_DATE="1641921698" LAST_MODIFIED="1641921700" TAGS="python programming, web development">Test</A>'

        bookmark.fill(markup)

        assert bookmark.tags == ["python programming", "web development"]


class TestParseFragment:
    """Tests for the parse_fragment function."""

    def test_parse_basic_a_tag(self):
        """Test parsing basic A tag."""
        content = '<A HREF="https://example.com" ADD_DATE="1641921698">Example</A>'

        text, attrib = parse_fragment(content)

        assert text == "Example"
        assert attrib == {
            'HREF': 'https://example.com',
            'ADD_DATE': '1641921698'
        }

    def test_parse_basic_h3_tag(self):
        """Test parsing basic H3 tag."""
        content = '<H3 ADD_DATE="1641921698" LAST_MODIFIED="1641921700">Folder Name</H3>'

        text, attrib = parse_fragment(content)

        assert text == "Folder Name"
        assert attrib == {
            'ADD_DATE': '1641921698',
            'LAST_MODIFIED': '1641921700'
        }

    def test_parse_complex_attributes(self):
        """Test parsing with multiple complex attributes."""
        content = '<A HREF="https://test.com/path?param=value" ADD_DATE="1641921698" LAST_MODIFIED="1641921700" LAST_VISIT="1641921699" TAGS="python, testing, web development">Complex Bookmark</A>'

        text, attrib = parse_fragment(content)

        assert text == "Complex Bookmark"
        assert attrib == {
            'HREF': 'https://test.com/path?param=value',
            'ADD_DATE': '1641921698',
            'LAST_MODIFIED': '1641921700',
            'LAST_VISIT': '1641921699',
            'TAGS': 'python, testing, web development'
        }

    def test_parse_no_attributes(self):
        """Test parsing tag with no attributes."""
        content = '<H3 >Simple Folder</H3>'  # Note: space required by regex

        text, attrib = parse_fragment(content)

        assert text == "Simple Folder"
        assert attrib == {}

    def test_parse_empty_content(self):
        """Test parsing tag with empty content."""
        content = '<A HREF="https://example.com"></A>'

        text, attrib = parse_fragment(content)

        assert text == ""
        assert attrib == {'HREF': 'https://example.com'}

    def test_parse_special_characters_in_text(self):
        """Test parsing with special characters in text content."""
        content = '<A HREF="https://example.com">Site with "quotes" & ampersands</A>'

        text, attrib = parse_fragment(content)

        assert text == 'Site with "quotes" & ampersands'
        assert attrib == {'HREF': 'https://example.com'}

    def test_parse_special_characters_in_attributes(self):
        """Test parsing with special characters in attribute values."""
        content = '<A HREF="https://example.com/path?q=test&amp;format=json" TAGS="web, api &amp; json">API Site</A>'

        text, attrib = parse_fragment(content)

        assert text == "API Site"
        assert attrib == {
            'HREF': 'https://example.com/path?q=test&amp;format=json',
            'TAGS': 'web, api &amp; json'
        }

    @pytest.mark.parser
    def test_parse_malformed_content_raises_error(self):
        """Test that malformed content raises ValueError."""
        malformed_content = [
            'Not a tag at all',
            '<A HREF="test"',  # Missing closing tag
            'HREF="test">Text</A>',  # Missing opening tag
            '<A >Text',  # Missing closing tag
            '<A HREF="test">Text</A',  # Missing > in closing tag
        ]

        for content in malformed_content:
            with pytest.raises(ValueError, match="Parse-error on content"):
                parse_fragment(content)

    def test_parse_case_sensitive_attributes(self):
        """Test that attribute parsing is case-sensitive."""
        content = '<A href="https://example.com" HREF="https://test.com">Test</A>'

        text, attrib = parse_fragment(content)

        assert text == "Test"
        # Both should be captured as separate attributes
        assert 'href' in attrib
        assert 'HREF' in attrib
        assert attrib['href'] == 'https://example.com'
        assert attrib['HREF'] == 'https://test.com'

    def test_parse_duplicate_attributes(self):
        """Test parsing with duplicate attribute names."""
        content = '<A HREF="first" HREF="second">Test</A>'

        text, attrib = parse_fragment(content)

        assert text == "Test"
        # Last occurrence should win
        assert attrib['HREF'] == 'second'

    def test_parse_attribute_order_preservation(self):
        """Test that attribute order doesn't affect parsing."""
        content1 = '<A ADD_DATE="123" HREF="https://example.com">Test</A>'
        content2 = '<A HREF="https://example.com" ADD_DATE="123">Test</A>'

        text1, attrib1 = parse_fragment(content1)
        text2, attrib2 = parse_fragment(content2)

        assert text1 == text2 == "Test"
        assert attrib1 == attrib2 == {
            'ADD_DATE': '123',
            'HREF': 'https://example.com'
        }
