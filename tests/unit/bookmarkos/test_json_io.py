# pylint: disable=missing-function-docstring, missing-class-docstring, invalid-name, no-member, import-error, line-too-long

"""Unit tests for bookmarkos.json_io module."""

import gzip
import json
from io import StringIO
from unittest.mock import Mock, patch
from bookmarkos.json_io import (
    BasicEncoder, BookmarksDecoder, read_content, read_plain_json,
    read_bookmarks_json, write_json_data
)

import pytest


class TestBasicEncoder:
    """Tests for the BasicEncoder class."""

    @pytest.mark.io
    def test_basic_encoder_handles_sets(self):
        """Test that BasicEncoder converts sets to sorted lists."""
        encoder = BasicEncoder()
        # pylint: disable=duplicate-value
        test_set = {3, 1, 4, 1, 5, 9, 2, 6}

        result = encoder.default(test_set)

        assert result == [1, 2, 3, 4, 5, 6, 9]  # Sorted and deduplicated
        assert isinstance(result, list)

    @pytest.mark.io
    def test_basic_encoder_handles_empty_set(self):
        """Test that BasicEncoder handles empty sets."""
        encoder = BasicEncoder()
        test_set = set()

        result = encoder.default(test_set)

        assert result == []
        assert isinstance(result, list)

    @pytest.mark.io
    def test_basic_encoder_handles_objects_with_dict(self):
        """Test that BasicEncoder converts objects to their __dict__."""
        encoder = BasicEncoder()

        class TestObject:
            def __init__(self):
                self.name = "test"
                self.value = 42

        test_obj = TestObject()
        result = encoder.default(test_obj)

        assert result == {"name": "test", "value": 42}

    @pytest.mark.io
    def test_basic_encoder_full_json_encoding(self):
        """Test full JSON encoding with sets and objects."""
        class TestObject:
            def __init__(self, name, tags):
                self.name = name
                self.tags = tags

        data = {
            "object": TestObject("test", {"python", "testing"}),
            "direct_set": {"a", "b", "c"},
            "normal_data": [1, 2, 3]
        }

        result = json.dumps(data, cls=BasicEncoder, sort_keys=True)
        parsed = json.loads(result)

        assert parsed["object"]["name"] == "test"
        assert parsed["object"]["tags"] == ["python", "testing"]
        assert parsed["direct_set"] == ["a", "b", "c"]
        assert parsed["normal_data"] == [1, 2, 3]


class TestBookmarksDecoder:
    """Tests for the BookmarksDecoder class."""

    @pytest.mark.io
    def test_bookmarks_decoder_creates_bookmark(self):
        """Test that BookmarksDecoder creates Bookmark objects."""
        decoder = BookmarksDecoder()

        bookmark_data = {
            "name": "Test Bookmark",
            "url": "https://example.com",
            "created": 1641921698,
            "updated": 1641921700,
            "visited": 1641921699,
            "tags": ["python", "testing"],
            "notes": "Test notes",
            "parent": ["root"]
        }

        with patch('bookmarkos.json_io.Bookmark') as MockBookmark:
            mock_bookmark = Mock()
            MockBookmark.return_value = mock_bookmark

            result = decoder.object_transform(bookmark_data)

            MockBookmark.assert_called_once_with(**bookmark_data)
            assert result == mock_bookmark

    @pytest.mark.io
    def test_bookmarks_decoder_creates_folder(self):
        """Test that BookmarksDecoder creates Folder objects."""
        decoder = BookmarksDecoder()

        folder_data = {
            "name": "Test Folder",
            "created": 1641921698,
            "updated": 1641921700,
            "parent": ["root"],
            "depth": 1,
            "content": []
        }

        with patch('bookmarkos.json_io.Folder') as MockFolder:
            mock_folder = Mock()
            MockFolder.return_value = mock_folder

            result = decoder.object_transform(folder_data)

            MockFolder.assert_called_once_with(**folder_data)
            assert result == mock_folder

    @pytest.mark.io
    def test_bookmarks_decoder_leaves_other_objects_unchanged(self):
        """Test that BookmarksDecoder doesn't change other objects."""
        decoder = BookmarksDecoder()

        other_data = {
            "name": "Something else",
            "value": 42,
            "items": ["a", "b", "c"]
        }

        result = decoder.object_transform(other_data)

        assert result == other_data

    @pytest.mark.io
    def test_bookmarks_decoder_full_json_decoding(self):
        """Test full JSON decoding with nested structure."""
        json_data = '''
        {
            "name": "Root",
            "content": [
                {
                    "name": "Bookmark",
                    "url": "https://example.com",
                    "tags": ["test"],
                    "created": 123456,
                    "updated": 123457
                },
                {
                    "name": "Subfolder",
                    "content": [],
                    "created": 123458,
                    "updated": 123459
                }
            ],
            "created": 123450,
            "updated": 123460
        }
        '''

        with patch('bookmarkos.json_io.Folder') as MockFolder, \
                patch('bookmarkos.json_io.Bookmark') as MockBookmark:

            mock_folder = Mock()
            mock_bookmark = Mock()
            MockFolder.return_value = mock_folder
            MockBookmark.return_value = mock_bookmark

            BookmarksDecoder()
            json.loads(json_data, cls=BookmarksDecoder)

            # Should create folder objects for items with 'content'
            assert MockFolder.call_count >= 1
            # Should create bookmark objects for items with 'tags'
            MockBookmark.assert_called_once()


class TestReadContent:
    """Tests for the read_content function."""

    @pytest.mark.io
    def test_read_content_from_file_handle(self):
        """Test reading content from an open file handle."""
        content = "Test file content"
        file_handle = StringIO(content)

        result = read_content(file_handle)

        assert result == content

    @pytest.mark.io
    def test_read_content_from_plain_file(self, temp_dir):
        """Test reading content from a plain text file."""
        content = "Test file content\nLine 2"
        test_file = temp_dir / "test.txt"
        test_file.write_text(content, encoding='utf-8')

        result = read_content(str(test_file))

        assert result == content

    @pytest.mark.io
    def test_read_content_from_gzip_file(self, temp_dir):
        """Test reading content from a gzip compressed file."""
        content = "Compressed test content\nLine 2"
        test_file = temp_dir / "test.txt.gz"

        with gzip.open(test_file, 'wt', encoding='utf-8') as f:
            f.write(content)

        result = read_content(str(test_file))

        assert result == content

    @pytest.mark.io
    def test_read_content_auto_detects_compression(self, temp_dir):
        """Test that read_content auto-detects compression by extension."""
        plain_content = "Plain text content"
        gzip_content = "Gzip compressed content"

        plain_file = temp_dir / "plain.txt"
        gzip_file = temp_dir / "compressed.txt.gz"

        plain_file.write_text(plain_content, encoding='utf-8')
        with gzip.open(gzip_file, 'wt', encoding='utf-8') as f:
            f.write(gzip_content)

        plain_result = read_content(str(plain_file))
        gzip_result = read_content(str(gzip_file))

        assert plain_result == plain_content
        assert gzip_result == gzip_content

    @pytest.mark.io
    def test_read_content_handles_utf8_encoding(self, temp_dir):
        """Test that read_content properly handles UTF-8 encoding."""
        content = "Unicode content: café, naïve, résumé, 中文"
        test_file = temp_dir / "unicode.txt"
        test_file.write_text(content, encoding='utf-8')

        result = read_content(str(test_file))

        assert result == content


class TestReadPlainJson:
    """Tests for the read_plain_json function."""

    @pytest.mark.io
    def test_read_plain_json_from_file(self, temp_dir):
        """Test reading plain JSON from a file."""
        data = {"name": "test", "value": 42, "items": [1, 2, 3]}
        test_file = temp_dir / "test.json"

        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        result = read_plain_json(str(test_file))

        assert result == data

    @pytest.mark.io
    def test_read_plain_json_from_compressed_file(self, temp_dir):
        """Test reading JSON from a gzip compressed file."""
        data = {"compressed": True, "values": [1, 2, 3]}
        test_file = temp_dir / "test.json.gz"

        with gzip.open(test_file, 'wt', encoding='utf-8') as f:
            json.dump(data, f)

        result = read_plain_json(str(test_file))

        assert result == data

    @pytest.mark.io
    def test_read_plain_json_from_file_handle(self):
        """Test reading JSON from a file handle."""
        data = {"source": "file_handle"}
        json_content = json.dumps(data)
        file_handle = StringIO(json_content)

        result = read_plain_json(file_handle)

        assert result == data

    @pytest.mark.io
    def test_read_plain_json_invalid_json_raises_error(self, temp_dir):
        """Test that invalid JSON raises an error."""
        invalid_json = '{"name": "test", "value":}'  # Missing value
        test_file = temp_dir / "invalid.json"
        test_file.write_text(invalid_json, encoding='utf-8')

        with pytest.raises(json.JSONDecodeError):
            read_plain_json(str(test_file))


class TestReadBookmarksJson:
    """Tests for the read_bookmarks_json function."""

    @pytest.mark.io
    def test_read_bookmarks_json_uses_decoder(self, temp_dir):
        """Test that read_bookmarks_json uses BookmarksDecoder."""
        bookmark_data = {
            "name": "Root",
            "content": [
                {
                    "name": "Test Bookmark",
                    "url": "https://example.com",
                    "tags": ["test"],
                    "created": 123456,
                    "updated": 123457
                }
            ],
            "created": 123450,
            "updated": 123460
        }

        test_file = temp_dir / "bookmarks.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(bookmark_data, f)

        with patch('bookmarkos.json_io.Folder') as MockFolder:
            mock_folder = Mock()
            MockFolder.return_value = mock_folder

            read_bookmarks_json(str(test_file))

            # Should create Folder objects due to 'content' attribute
            MockFolder.assert_called()


class TestWriteJsonData:
    """Tests for the write_json_data function."""

    @pytest.mark.io
    def test_write_json_data_to_plain_file(self, temp_dir):
        """Test writing JSON data to a plain file."""
        data = {"name": "test", "value": 42}
        test_file = temp_dir / "output.json"

        write_json_data(data, str(test_file))

        # Verify file was written correctly
        with open(test_file, 'r', encoding='utf-8') as f:
            result = json.load(f)

        assert result == data

    @pytest.mark.io
    def test_write_json_data_to_compressed_file(self, temp_dir):
        """Test writing JSON data to a gzip compressed file."""
        data = {"compressed": True, "values": [1, 2, 3]}
        test_file = temp_dir / "output.json.gz"

        write_json_data(data, str(test_file))

        # Verify compressed file was written correctly
        with gzip.open(test_file, 'rt', encoding='utf-8') as f:
            result = json.load(f)

        assert result == data

    @pytest.mark.io
    def test_write_json_data_to_file_handle(self):
        """Test writing JSON data to an open file handle."""
        data = {"target": "file_handle"}
        file_handle = StringIO()

        write_json_data(data, file_handle)

        result_json = file_handle.getvalue()
        result = json.loads(result_json)

        assert result == data

    @pytest.mark.io
    def test_write_json_data_with_custom_json_args(self, temp_dir):
        """Test writing JSON with custom JSON arguments."""
        data = {"name": "test", "value": 42}
        test_file = temp_dir / "formatted.json"

        write_json_data(data, str(test_file), json={
                        "indent": 2, "sort_keys": True})

        # Verify formatting
        content = test_file.read_text(encoding='utf-8')
        assert "  " in content  # Should be indented
        assert content.index('"name"') < content.index(
            '"value"')  # Should be sorted

    @pytest.mark.io
    def test_write_json_data_with_custom_gzip_args(self, temp_dir):
        """Test writing compressed JSON with custom gzip arguments."""
        data = {"compression": "custom"}
        test_file = temp_dir / "custom_compressed.json.gz"

        write_json_data(data, str(test_file), gzip={"compresslevel": 1})

        # Verify file exists and can be read
        with gzip.open(test_file, 'rt', encoding='utf-8') as f:
            result = json.load(f)

        assert result == data

    @pytest.mark.io
    def test_write_json_data_uses_basic_encoder(self, temp_dir):
        """Test that write_json_data uses BasicEncoder for sets."""
        data = {
            "name": "test",
            "tags": {"python", "testing", "json"},
            "numbers": {1, 2, 3}
        }
        test_file = temp_dir / "with_sets.json"

        write_json_data(data, str(test_file))

        # Read back and verify sets were converted to sorted lists
        with open(test_file, 'r', encoding='utf-8') as f:
            result = json.load(f)

        assert isinstance(result["tags"], list)
        assert sorted(result["tags"]) == result["tags"]  # Should be sorted
        assert isinstance(result["numbers"], list)
        assert sorted(result["numbers"]) == result["numbers"]

    @pytest.mark.io
    def test_write_json_data_ensures_utf8(self, temp_dir):
        """Test that write_json_data properly handles UTF-8 content."""
        data = {"message": "Unicode: café, naïve, 中文"}
        test_file = temp_dir / "unicode.json"

        write_json_data(data, str(test_file))

        # Verify Unicode content is preserved
        with open(test_file, 'r', encoding='utf-8') as f:
            result = json.load(f)

        assert result == data
        assert "café" in result["message"]
        assert "中文" in result["message"]


class TestJsonIoIntegration:
    """Integration tests for JSON I/O operations."""

    @pytest.mark.integration
    @pytest.mark.io
    def test_write_and_read_roundtrip(self, temp_dir):
        """Test complete write and read roundtrip."""
        original_data = {
            "name": "Root Folder",
            "content": [
                {
                    "name": "Test Bookmark",
                    "url": "https://example.com",
                    "tags": {"python", "testing"},  # Set will be converted
                    "created": 1641921698,
                    "notes": "Test bookmark"
                }
            ],
            "created": 1641921600
        }

        test_file = temp_dir / "roundtrip.json"

        # Write data
        write_json_data(original_data, str(test_file))

        # Read back as plain JSON
        result_data = read_plain_json(str(test_file))

        # Verify data integrity (sets should be converted to lists)
        assert result_data["name"] == original_data["name"]
        assert result_data["content"][0]["name"] == original_data["content"][0]["name"]
        assert result_data["content"][0]["url"] == original_data["content"][0]["url"]
        assert isinstance(result_data["content"][0]["tags"], list)
        assert sorted(result_data["content"][0]["tags"]) == [
            "python", "testing"]

    @pytest.mark.integration
    @pytest.mark.io
    def test_compression_roundtrip(self, temp_dir):
        """Test roundtrip with compression."""
        data = {"large_data": "x" * 1000, "numbers": list(range(100))}

        compressed_file = temp_dir / "data.json.gz"
        plain_file = temp_dir / "data.json"

        # Write to both compressed and plain
        write_json_data(data, str(compressed_file))
        write_json_data(data, str(plain_file))

        # Read from both
        compressed_result = read_plain_json(str(compressed_file))
        plain_result = read_plain_json(str(plain_file))

        # Should be identical
        assert compressed_result == plain_result == data

        # Compressed file should be smaller
        assert compressed_file.stat().st_size < plain_file.stat().st_size
